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
    """Create (or reset the password of) the admin user from env vars on every boot.

    Render's free tier has no Shell access to run `create_user.py` by hand,
    so this is the only way to get/reset a login without a paid instance.
    Always syncs this specific username's password to match the env var,
    so it's safe to redeploy repeatedly and self-heals any stale state.
    """
    username = os.environ.get("PMDASH_ADMIN_USERNAME")
    password = os.environ.get("PMDASH_ADMIN_PASSWORD")
    if not username or not password:
        return
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.hashed_password = hash_password(password)
        else:
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
