from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.models import init_db
from app.routers import photos, admin
from app.routers.admin import limiter
from app.storage import STORAGE_DIR, PUBLIC_PATH_PREFIX

app = FastAPI(title="Anant Shukla Photography API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
# Change this to your real frontend origin before going live. "*" is fine
# only for local testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- static files: uploaded/watermarked photos, admin panel, and the public site ---
app.mount(PUBLIC_PATH_PREFIX, StaticFiles(directory=STORAGE_DIR), name="photos")
app.mount("/admin-ui", StaticFiles(directory="static", html=True), name="admin-ui")

app.include_router(photos.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/status")
def status():
    return {"status": "ok", "docs": "/docs", "admin_panel": "/admin-ui"}


# Mounted LAST and at "/" so it acts as a catch-all for the public site —
# routers and other mounts above are matched first since they're registered first.
app.mount("/", StaticFiles(directory="public", html=True), name="public-site")
