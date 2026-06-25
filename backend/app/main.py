import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .database import Base, SessionLocal, engine
from .models import User
from .routers import auth, data, notes, records
from .security import hash_password

Base.metadata.create_all(bind=engine)


def _ensure_seed_admin():
    """Auto-create an admin user from env vars on first boot.

    Render's free tier has no Shell access to run `create_user.py` by hand,
    so this is the only way to get a first login without a paid instance.
    No-ops once any user already exists.
    """
    username = os.environ.get("PMDASH_ADMIN_USERNAME")
    password = os.environ.get("PMDASH_ADMIN_PASSWORD")
    if not username or not password:
        return
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(username=username, hashed_password=hash_password(password)))
            db.commit()
    finally:
        db.close()


_ensure_seed_admin()

app = FastAPI(title="Performance Matrix Dashboard")

app.include_router(auth.router)
app.include_router(data.router)
app.include_router(notes.router)
app.include_router(records.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent
INDEX_FILE = FRONTEND_DIR / "index.html"


@app.get("/")
def serve_index():
    return FileResponse(INDEX_FILE)
