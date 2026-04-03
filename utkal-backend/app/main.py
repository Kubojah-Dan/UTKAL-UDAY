from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import asyncio
from pathlib import Path

# import routers
from app.api import sync as sync_router
from app.api import content as content_router
from app.api import dashboard as dashboard_router
from app.api import recommend as recommend_router
from app.api import auth as auth_router
from app.api import tools as tools_router
from app.api import student as student_router

load_dotenv()

app = FastAPI(title="Utkal Uday API")

# CORS - for dev allow all origins; lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(sync_router.router, prefix="")
app.include_router(content_router.router, prefix="")
app.include_router(dashboard_router.router, prefix="")
app.include_router(recommend_router.router, prefix="")
app.include_router(auth_router.router, prefix="")
app.include_router(tools_router.router, prefix="")
app.include_router(student_router.router, prefix="")

# Serve static content (problem JSONs and assets) under /content
content_dir = os.path.join(os.path.dirname(__file__), "content")
os.makedirs(os.path.abspath(content_dir), exist_ok=True)
app.mount("/content", StaticFiles(directory=content_dir), name="content")

# Serve XES3G5M question/analysis images
xes_images_dir = Path(__file__).resolve().parents[1] / "data" / "XES3G5M" / "metadata" / "images"
if xes_images_dir.exists():
    app.mount("/xes-images", StaticFiles(directory=str(xes_images_dir)), name="xes-images")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _startup_localization_languages() -> list[str]:
    raw = os.getenv("UTKAL_STARTUP_LOCALIZATION_LANGUAGES", "hi,ta,te,or")
    return [lang.strip() for lang in raw.split(",") if lang.strip()]


@app.on_event("startup")
async def startup_event():
    """Optionally warm question localizations after startup without blocking requests."""
    if not _env_flag("UTKAL_STARTUP_LOCALIZATION_ENABLED", default=False):
        print("[startup] Localization warm-up disabled; missing translations will be queued on demand.")
        return

    app.state.localization_warmup_task = asyncio.create_task(_warm_question_localizations())


async def _warm_question_localizations():
    """Queue a small localization warm-up after startup without blocking the event loop."""
    try:
        from app.core.database import questions_collection
        from app.core.question_localization import queue_question_localization

        delay_seconds = max(0.0, float(os.getenv("UTKAL_STARTUP_LOCALIZATION_DELAY_SECONDS", "10")))
        max_questions = max(0, int(os.getenv("UTKAL_STARTUP_LOCALIZATION_MAX_QUESTIONS", "12")))
        batch_pause_seconds = max(0.0, float(os.getenv("UTKAL_STARTUP_LOCALIZATION_BATCH_PAUSE_SECONDS", "0.25")))
        batch_size = max(1, int(os.getenv("UTKAL_STARTUP_LOCALIZATION_BATCH_SIZE", "3")))
        target_langs = _startup_localization_languages()

        if delay_seconds:
            await asyncio.sleep(delay_seconds)

        if not target_langs or max_questions <= 0:
            print("[startup] Localization warm-up skipped; no startup languages or questions configured.")
            return

        cursor = questions_collection.find(
            {
                "approved": True,
                "status": "active",
                "$or": [
                    {"language_variants": {"$exists": False}},
                    {"language_variants": None},
                    {"language_variants": {}},
                ],
            }
        ).limit(max_questions)
        pending_questions = await cursor.to_list(length=max_questions)
        if not pending_questions:
            print("[startup] No startup localization warm-up needed.")
            return

        print(
            f"[startup] Queueing localization warm-up for {len(pending_questions)} questions "
            f"to {target_langs} after {delay_seconds:.1f}s delay."
        )

        for index, question in enumerate(pending_questions, start=1):
            question.pop("_id", None)
            queue_question_localization(question, target_langs=target_langs)
            if index % batch_size == 0:
                await asyncio.sleep(batch_pause_seconds)

        print("[startup] Localization warm-up queued.")
    except Exception as e:
        print(f"[startup] Localization warm-up error: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "utkal-backend"}
