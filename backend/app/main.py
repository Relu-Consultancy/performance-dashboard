from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .database import Base, engine
from .routers import auth, data, notes, records

Base.metadata.create_all(bind=engine)

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
