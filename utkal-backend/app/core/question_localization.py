import asyncio
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.core.database import question_localizations_collection

SUPPORTED_LANGUAGE_CODES: Tuple[str, ...] = ("en", "hi", "ta", "te", "or")
TRANSLATABLE_FIELDS: Tuple[str, ...] = (
    "question",
    "passage",
    "instructions",
    "explanation",
    "hint",
)
TRANSLATION_CACHE: Dict[Tuple[str, str, Tuple[str, ...]], Dict[str, Dict]] = {}
LOCALIZATION_TASKS: Dict[Tuple[str, str, Tuple[str, ...]], asyncio.Task] = {}
LOCALIZATION_SEMAPHORE: Optional[asyncio.Semaphore] = None


def normalize_language_code(language: object) -> str:
    key = str(language or "").strip().lower()
    aliases = {
        "": "en",
        "en": "en",
        "en-us": "en",
        "en-gb": "en",
        "english": "en",
        "hi": "hi",
        "hindi": "hi",
        "ta": "ta",
        "tamil": "ta",
        "te": "te",
        "telugu": "te",
        "or": "or",
        "oriya": "or",
        "odia": "or",
        "od": "or",
        "od-in": "or",
        "zh": "zh-CN",
        "zh-cn": "zh-CN",
        "zh-hans": "zh-CN",
        "chinese": "zh-CN",
        "simplified chinese": "zh-CN",
    }
    return aliases.get(key, str(language or "en").strip() or "en")


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _normalize_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _question_id(question: Dict) -> str:
    return str(question.get("id") or "").strip()


def _get_localization_semaphore() -> asyncio.Semaphore:
    global LOCALIZATION_SEMAPHORE
    if LOCALIZATION_SEMAPHORE is None:
        concurrency = max(1, int(os.getenv("UTKAL_LOCALIZATION_CONCURRENCY", "1")))
        LOCALIZATION_SEMAPHORE = asyncio.Semaphore(concurrency)
    return LOCALIZATION_SEMAPHORE


def _extract_variant_payload(question: Dict) -> Dict:
    payload = {field: _normalize_text(question.get(field)) for field in TRANSLATABLE_FIELDS}
    payload["options"] = _normalize_list(question.get("options"))
    payload["expected_points"] = _normalize_list(question.get("expected_points"))
    return payload


def _variant_signature(payload: Dict) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    return (
        tuple(_normalize_text(payload.get(field)).strip().casefold() for field in TRANSLATABLE_FIELDS),
        tuple(item.strip().casefold() for item in _normalize_list(payload.get("options"))),
        tuple(item.strip().casefold() for item in _normalize_list(payload.get("expected_points"))),
    )


def _is_meaningful_variant(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    for field in TRANSLATABLE_FIELDS:
        if str(payload.get(field) or "").strip():
            return True
    if payload.get("options"):
        return True
    if payload.get("expected_points"):
        return True
    return False


def _normalize_variants(variants: object) -> Dict[str, Dict]:
    normalized: Dict[str, Dict] = {}
    if not isinstance(variants, dict):
        return normalized

    for language, payload in variants.items():
        lang = normalize_language_code(language)
        if not isinstance(payload, dict):
            continue

        candidate = {
            field: _normalize_text(payload.get(field))
            for field in TRANSLATABLE_FIELDS
        }
        candidate["options"] = _normalize_list(payload.get("options"))
        candidate["expected_points"] = _normalize_list(payload.get("expected_points"))

        if _is_meaningful_variant(candidate):
            normalized[lang] = candidate

    return normalized


def _merge_variants(base: Dict[str, Dict], incoming: Dict[str, Dict]) -> Dict[str, Dict]:
    merged = copy.deepcopy(base)
    for language, payload in incoming.items():
        lang = normalize_language_code(language)
        existing = merged.get(lang, {})
        next_payload = {
            field: _normalize_text(payload.get(field) or existing.get(field))
            for field in TRANSLATABLE_FIELDS
        }
        next_payload["options"] = _normalize_list(payload.get("options")) or _normalize_list(existing.get("options"))
        next_payload["expected_points"] = _normalize_list(payload.get("expected_points")) or _normalize_list(existing.get("expected_points"))
        if _is_meaningful_variant(next_payload):
            merged[lang] = next_payload
    return merged


def _ensure_source_variant(question: Dict, variants: Dict[str, Dict], source_lang: str) -> Dict[str, Dict]:
    if source_lang not in variants or not _is_meaningful_variant(variants.get(source_lang)):
        variants[source_lang] = _extract_variant_payload(question)
    return variants


def _filter_untranslated_variants(
    variants: Dict[str, Dict],
    source_lang: str,
    source_payload: Dict,
    target_langs: Tuple[str, ...],
) -> Dict[str, Dict]:
    filtered: Dict[str, Dict] = {}
    source_signature = _variant_signature(source_payload)
    target_set = set(target_langs)

    for language, payload in variants.items():
        if language == source_lang:
            filtered[language] = payload
            continue
        if language in target_set and _variant_signature(payload) == source_signature:
            continue
        filtered[language] = payload

    return filtered


def _dedupe_languages(languages: Optional[Iterable[str]]) -> Tuple[str, ...]:
    ordered: List[str] = []
    seen = set()
    for language in languages or SUPPORTED_LANGUAGE_CODES:
        lang = normalize_language_code(language)
        if lang in seen:
            continue
        seen.add(lang)
        ordered.append(lang)
    return tuple(ordered)


def _translation_payload(question: Dict, source_lang: str) -> str:
    payload = _extract_variant_payload(question)
    payload["language"] = source_lang
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _translation_source_hash(question: Dict, source_lang: str) -> str:
    return hashlib.md5(_translation_payload(question, source_lang).encode("utf8")).hexdigest()


def _missing_languages(variants: Dict[str, Dict], target_langs: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple(language for language in target_langs if language not in variants)


def _translate_variants_sync(payload_json: str, source_lang: str, target_langs: Tuple[str, ...]) -> Dict[str, Dict]:
    cache_key = (payload_json, source_lang, target_langs)
    cached = TRANSLATION_CACHE.get(cache_key)
    if cached:
        return copy.deepcopy(cached)

    payload = json.loads(payload_json)
    payload["language"] = source_lang
    source_payload = _extract_variant_payload(payload)

    if not target_langs:
        return {}

    if os.getenv("GROQ_API_KEY"):
        try:
            from app.core.groq_translator import translate_question as groq_translate_question

            translated = groq_translate_question(copy.deepcopy(payload), list(target_langs))
            variants = _filter_untranslated_variants(
                _normalize_variants(translated.get("language_variants")),
                source_lang,
                source_payload,
                target_langs,
            )
            if variants:
                TRANSLATION_CACHE[cache_key] = copy.deepcopy(variants)
                return variants
        except Exception as exc:
            print(f"[localization] Groq translation failed: {exc}")

    if source_lang == "en":
        if os.getenv("SARVAM_API_KEY"):
            try:
                from app.core.translation import translate_question as sarvam_translate_question

                translated = sarvam_translate_question(copy.deepcopy(payload), list(target_langs))
                variants = _filter_untranslated_variants(
                    _normalize_variants(translated.get("language_variants")),
                    source_lang,
                    source_payload,
                    target_langs,
                )
                if variants:
                    TRANSLATION_CACHE[cache_key] = copy.deepcopy(variants)
                    return variants
            except Exception as exc:
                print(f"[localization] Sarvam translation failed: {exc}")

        try:
            from app.core.indictrans_translator import translate_question as indictrans_translate_question

            translated = indictrans_translate_question(copy.deepcopy(payload), list(target_langs))
            variants = _filter_untranslated_variants(
                _normalize_variants(translated.get("language_variants")),
                source_lang,
                source_payload,
                target_langs,
            )
            if variants:
                TRANSLATION_CACHE[cache_key] = copy.deepcopy(variants)
                return variants
        except Exception as exc:
            print(f"[localization] IndicTrans translation failed: {exc}")

    return {}


def ensure_question_localization(
    question: Optional[Dict],
    target_langs: Optional[Sequence[str]] = None,
) -> Optional[Dict]:
    if not isinstance(question, dict):
        return question

    localized = copy.deepcopy(question)
    source_lang = normalize_language_code(localized.get("language") or "en")

    variants = _normalize_variants(localized.get("language_variants"))
    variants = _ensure_source_variant(localized, variants, source_lang)

    requested = _dedupe_languages(target_langs) if target_langs is not None else ()
    if requested:
        variants = {
            language: payload
            for language, payload in variants.items()
            if language == source_lang or language in requested
        }
        variants = _ensure_source_variant(localized, variants, source_lang)

    localized["language_variants"] = variants
    return localized


async def _load_cached_variants(question_id: str, source_hash: str) -> Dict[str, Dict]:
    if not question_id:
        return {}

    try:
        record = await question_localizations_collection.find_one(
            {"question_id": question_id, "source_hash": source_hash}
        )
    except Exception as exc:
        print(f"[localization] Failed to load cached variants for {question_id}: {exc}")
        return {}

    return _normalize_variants(record.get("language_variants")) if record else {}


async def _persist_cached_variants(
    question_id: str,
    source_hash: str,
    source_lang: str,
    variants: Dict[str, Dict],
) -> None:
    if not question_id or not variants:
        return

    payload = {
        "question_id": question_id,
        "source_hash": source_hash,
        "source_language": source_lang,
        "language_variants": variants,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await question_localizations_collection.update_one(
            {"question_id": question_id, "source_hash": source_hash},
            {"$set": payload},
            upsert=True,
        )
    except Exception as exc:
        print(f"[localization] Failed to persist variants for {question_id}: {exc}")


async def _run_localization_job(question: Dict, source_lang: str, target_langs: Tuple[str, ...], source_hash: str) -> None:
    question_id = _question_id(question)
    try:
        async with _get_localization_semaphore():
            translated = await asyncio.to_thread(
                _translate_variants_sync,
                _translation_payload(question, source_lang),
                source_lang,
                target_langs,
            )
        if not translated:
            return

        base_variants = _normalize_variants(question.get("language_variants"))
        current_cached = await _load_cached_variants(question_id, source_hash)
        merged = _merge_variants(_merge_variants(base_variants, current_cached), translated)
        await _persist_cached_variants(question_id, source_hash, source_lang, merged)
    except Exception as exc:
        print(f"[localization] Background localization failed for {question_id}: {exc}")
    finally:
        LOCALIZATION_TASKS.pop((question_id, source_hash, target_langs), None)


def queue_question_localization(question: Optional[Dict], target_langs: Optional[Sequence[str]] = None) -> None:
    if not isinstance(question, dict):
        return
    if target_langs is None:
        return

    source_lang = normalize_language_code(question.get("language") or "en")
    normalized = ensure_question_localization(question)
    question_id = _question_id(normalized)
    source_hash = _translation_source_hash(normalized, source_lang)
    variants = _normalize_variants(normalized.get("language_variants"))
    missing = _missing_languages(variants, _dedupe_languages(target_langs))

    if not question_id or not missing:
        return

    task_key = (question_id, source_hash, missing)
    existing = LOCALIZATION_TASKS.get(task_key)
    if existing and not existing.done():
        return

    try:
        LOCALIZATION_TASKS[task_key] = asyncio.create_task(
            _run_localization_job(normalized, source_lang, missing, source_hash)
        )
    except RuntimeError:
        # No running event loop. Skip queuing rather than blocking the caller.
        return


async def prepare_question_for_delivery(
    question: Optional[Dict],
    target_langs: Optional[Sequence[str]] = None,
    queue_missing: bool = False,
) -> Optional[Dict]:
    if not isinstance(question, dict):
        return question

    localized = ensure_question_localization(question)
    source_lang = normalize_language_code(localized.get("language") or "en")
    source_hash = _translation_source_hash(localized, source_lang)

    cached_variants = await _load_cached_variants(_question_id(localized), source_hash)
    if cached_variants:
        localized["language_variants"] = _merge_variants(
            _normalize_variants(localized.get("language_variants")),
            cached_variants,
        )

    if queue_missing:
        queue_question_localization(localized, target_langs=target_langs)

    return localized


async def prepare_questions_for_delivery(
    questions: Optional[Sequence[Dict]],
    target_langs: Optional[Sequence[str]] = None,
    queue_missing: bool = False,
    queue_limit: Optional[int] = None,
) -> List[Dict]:
    if not questions:
        return []

    prepared: List[Dict] = []
    for index, question in enumerate(questions):
        should_queue = queue_missing and (queue_limit is None or index < queue_limit)
        prepared_question = await prepare_question_for_delivery(
            question,
            target_langs=target_langs,
            queue_missing=should_queue,
        )
        if isinstance(prepared_question, dict):
            prepared.append(prepared_question)
    return prepared
