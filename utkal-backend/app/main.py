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


@app.on_event("startup")
async def startup_event():
    """Ensure MongoDB questions are translated on startup"""
    asyncio.create_task(_ensure_translations())


async def _ensure_translations():
    """Background task: translate any questions missing translations"""
    try:
        from app.core.database import questions_collection
        from app.core.groq_translator import translate_questions_batch

        cursor = questions_collection.find(
            {"approved": True, "status": "active",
             "$or": [{"language_variants": {"$exists": False}},
                     {"language_variants": None},
                     {"language_variants": {}}]}
        )
        untranslated = await cursor.to_list(length=50)  # process up to 50 on startup
        if not untranslated:
            return

        print(f"[startup] Translating {len(untranslated)} questions in background...")
        for i in range(0, len(untranslated), 5):
            batch = untranslated[i:i+5]
            try:
                translated = translate_questions_batch(batch, ["hi", "ta", "te", "or"])
                for q in translated:
                    await questions_collection.update_one(
                        {"id": q["id"]},
                        {"$set": {"language_variants": q.get("language_variants", {})}}
                    )
                await asyncio.sleep(2)  # respect rate limits
            except Exception as e:
                print(f"[startup] Translation batch error: {e}")
                break
        print(f"[startup] Background translation done")
    except Exception as e:
        print(f"[startup] Translation check error: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "utkal-backend"}
