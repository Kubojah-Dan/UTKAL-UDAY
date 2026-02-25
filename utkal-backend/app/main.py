from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# import routers
from app.api import sync as sync_router
from app.api import content as content_router
from app.api import dashboard as dashboard_router
from app.api import recommend as recommend_router
from app.api import auth as auth_router

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

# Serve static content (problem JSONs and assets) under /content
content_dir = os.path.join(os.path.dirname(__file__), "content")
# ensure folder exists
os.makedirs(os.path.abspath(content_dir), exist_ok=True)
app.mount("/content", StaticFiles(directory=content_dir), name="content")

# Serve XES3G5M question/analysis images
xes_images_dir = Path(__file__).resolve().parents[1] / "data" / "XES3G5M" / "metadata" / "images"
if xes_images_dir.exists():
    app.mount("/xes-images", StaticFiles(directory=str(xes_images_dir)), name="xes-images")


@app.get("/health")
def health():
    return {"status": "ok", "service": "utkal-backend"}
