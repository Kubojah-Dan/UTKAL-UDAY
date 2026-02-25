import hashlib
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[2]
XES_BASE = BACKEND_ROOT / "data" / "XES3G5M"
QUESTIONS_FILE = XES_BASE / "metadata" / "questions.json"
IMAGES_DIR = XES_BASE / "metadata" / "images"

IMAGE_TOKEN_PATTERN = re.compile(r"(?:question|analysis)_\d+-image_\d+")
WHITESPACE_PATTERN = re.compile(r"\s+")

MCQ_LABEL_UNICODE = "\u5355\u9009"


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", "\n").replace("\u200b", " ")
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def _strip_image_tokens(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", IMAGE_TOKEN_PATTERN.sub(" ", text)).strip()


def _strip_math_markers(text: str) -> str:
    cleaned = _clean_text(text).replace("$$", "")
    return cleaned.strip("$").strip()


def _stable_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf8")).hexdigest()


def _stable_grade(seed: str) -> int:
    return (int(_stable_hash(seed)[:8], 16) % 12) + 1


def _slug_or_hash(label: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if ascii_slug:
        return ascii_slug
    return f"skill-{_stable_hash(label)[:10]}"


def _parse_route(raw_routes: object) -> List[str]:
    if not raw_routes:
        return []
    if isinstance(raw_routes, list):
        route = raw_routes[0] if raw_routes else ""
    else:
        route = str(raw_routes)
    return [seg for seg in (_clean_text(s) for s in str(route).split("----")) if seg]


def _normalize_options(options: object) -> List[str]:
    if not isinstance(options, dict):
        return []
    out = []
    for key in sorted(options.keys(), key=lambda x: str(x)):
        value = _clean_text(options.get(key))
        if value:
            out.append(value)
    return out


def _normalize_answers(answer: object, options: object) -> List[str]:
    option_map = options if isinstance(options, dict) else {}
    if isinstance(answer, list):
        raw_answers = answer
    elif answer is None:
        raw_answers = []
    else:
        raw_answers = [answer]

    accepted: List[str] = []
    for item in raw_answers:
        value = _strip_math_markers(str(item))
        if not value:
            continue
        if value in option_map:
            mapped = _clean_text(option_map[value])
            if mapped:
                accepted.append(mapped)
        accepted.append(value)

    deduped: List[str] = []
    seen = set()
    for ans in accepted:
        key = ans.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ans)
    return deduped


def _extract_image_names(text: str) -> List[str]:
    return [f"{token}.png" for token in IMAGE_TOKEN_PATTERN.findall(text or "")]


def _build_media(content: str, analysis: str) -> Tuple[List[Dict], List[str], List[str]]:
    q_names = _extract_image_names(content)
    a_names = _extract_image_names(analysis)

    media: List[Dict] = []
    seen = set()
    question_urls: List[str] = []
    analysis_urls: List[str] = []

    for name in q_names:
        if name in seen:
            continue
        if not (IMAGES_DIR / name).exists():
            continue
        seen.add(name)
        url = f"/xes-images/{name}"
        media.append({"kind": "image", "role": "question", "name": name, "url": url})
        question_urls.append(url)

    for name in a_names:
        if name in seen:
            continue
        if not (IMAGES_DIR / name).exists():
            continue
        seen.add(name)
        url = f"/xes-images/{name}"
        media.append({"kind": "image", "role": "analysis", "name": name, "url": url})
        analysis_urls.append(url)

    return media, question_urls, analysis_urls


def _difficulty_from_grade(grade: int, answer_parts: int, has_question_image: bool) -> str:
    if grade <= 4:
        base = "easy"
    elif grade <= 8:
        base = "medium"
    else:
        base = "hard"
    if has_question_image and base == "easy":
        base = "medium"
    if answer_parts > 1 and base == "easy":
        base = "medium"
    return base


def _is_mcq(raw_type: str, options: object) -> bool:
    if isinstance(options, dict) and bool(options):
        return True
    return MCQ_LABEL_UNICODE in (raw_type or "")


@lru_cache(maxsize=1)
def _load_raw_questions() -> Dict[str, Dict]:
    if not QUESTIONS_FILE.exists():
        return {}
    return json.loads(QUESTIONS_FILE.read_text(encoding="utf8"))


@lru_cache(maxsize=1)
def _build_index() -> Dict[str, Dict]:
    raw = _load_raw_questions()
    if not raw:
        return {}

    by_route: Dict[str, str] = {}
    out: Dict[str, Dict] = {}

    for raw_qid, payload in raw.items():
        qid = int(raw_qid)
        content_raw = _clean_text(payload.get("content"))
        analysis_raw = _clean_text(payload.get("analysis"))
        content = _strip_image_tokens(content_raw)
        analysis = _strip_image_tokens(analysis_raw)

        route = _parse_route(payload.get("kc_routes"))
        route_key = "|".join(route) if route else f"route:{qid}"
        skill_label = route[-1] if route else f"Concept {qid}"

        if route_key not in by_route:
            by_route[route_key] = f"xes-{_slug_or_hash(skill_label)}-{_stable_hash(route_key)[:6]}"
        skill_id = by_route[route_key]

        options_raw = payload.get("options") if isinstance(payload.get("options"), dict) else {}
        options = _normalize_options(options_raw)
        accepted_answers = _normalize_answers(payload.get("answer"), options_raw)

        media, question_images, analysis_images = _build_media(content_raw, analysis_raw)
        has_question_image = len(question_images) > 0
        grade = _stable_grade(route_key)

        question_text = content
        if has_question_image:
            question_text = f"{question_text}\n[Refer to the attached question image(s).]"

        hint = ""
        if analysis:
            hint = analysis.split("。")[0].split(".")[0].strip()
        if len(hint) > 180:
            hint = hint[:177].rstrip() + "..."

        converted = {
            "id": f"XES-{qid}",
            "source": "XES3G5M",
            "source_qid": qid,
            "subject": "Mathematics",
            "grade": grade,
            "skill_id": skill_id,
            "skill_label": skill_label,
            "skill_route": route,
            "route_depth": len(route),
            "difficulty": _difficulty_from_grade(grade, len(accepted_answers), has_question_image),
            "language": "zh-CN",
            "type": "mcq" if _is_mcq(_clean_text(payload.get("type")), options_raw) else "text",
            "question": question_text,
            "options": options,
            "answer": accepted_answers[0] if accepted_answers else "",
            "accepted_answers": accepted_answers,
            "hint": hint,
            "explanation": analysis,
            "media": media,
            "question_images": question_images,
            "analysis_images": analysis_images,
            "has_image_question": has_question_image,
            "has_image_analysis": len(analysis_images) > 0,
        }

        out[converted["id"]] = converted

    return out


def get_xes_questions() -> List[Dict]:
    return list(_build_index().values())


def get_xes_question_by_id(question_id: str) -> Optional[Dict]:
    qid = str(question_id or "").strip()
    if not qid:
        return None

    index = _build_index()
    if qid in index:
        return index[qid]

    # Support plain integer ID lookups by normalizing to XES-prefixed IDs.
    if qid.isdigit():
        return index.get(f"XES-{int(qid)}")

    return None


def refresh_xes_cache() -> None:
    _load_raw_questions.cache_clear()
    _build_index.cache_clear()


@lru_cache(maxsize=1)
def get_xes_dataset_summary() -> Dict:
    raw = _load_raw_questions()
    if not raw:
        return {
            "present": False,
            "base_path": str(XES_BASE),
            "question_count": 0,
            "image_count": 0,
        }

    type_counter: Counter = Counter()
    options_mcq = 0
    has_question_image = 0
    has_analysis_image = 0
    multi_route = 0
    multi_answer = 0
    route_leaf_counter: Counter = Counter()

    for payload in raw.values():
        raw_type = _clean_text(payload.get("type"))
        type_counter[raw_type] += 1

        options = payload.get("options")
        if isinstance(options, dict) and options:
            options_mcq += 1

        content = str(payload.get("content") or "")
        analysis = str(payload.get("analysis") or "")
        if IMAGE_TOKEN_PATTERN.search(content):
            has_question_image += 1
        if IMAGE_TOKEN_PATTERN.search(analysis):
            has_analysis_image += 1

        routes = _parse_route(payload.get("kc_routes"))
        if len(routes) > 1:
            multi_route += 1
        if routes:
            route_leaf_counter[routes[-1]] += 1

        answers = payload.get("answer")
        if isinstance(answers, list) and len(answers) > 1:
            multi_answer += 1

    image_count = 0
    if IMAGES_DIR.exists():
        image_count = len(list(IMAGES_DIR.glob("*.png")))

    top_skill_labels = [{"skill_label": k, "question_count": v} for k, v in route_leaf_counter.most_common(15)]

    return {
        "present": True,
        "base_path": str(XES_BASE),
        "question_count": len(raw),
        "image_count": image_count,
        "question_image_questions": has_question_image,
        "analysis_image_questions": has_analysis_image,
        "multi_route_questions": multi_route,
        "multi_answer_questions": multi_answer,
        "question_types": dict(type_counter),
        "mcq_with_options_count": options_mcq,
        "top_skill_labels": top_skill_labels,
        "converted_question_count": len(_build_index()),
    }
