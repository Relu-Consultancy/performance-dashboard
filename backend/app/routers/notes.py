from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import EmployeeNote, User
from ..schemas import NoteIn

router = APIRouter(prefix="/api", tags=["notes"])


@router.get("/notes")
def list_notes(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(EmployeeNote).all()
    out: dict[str, dict[str, dict]] = {}
    for r in rows:
        out.setdefault(r.employee_name, {})[r.year_month] = {
            "note": r.note,
            "updated_by": r.updated_by,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
    return out


@router.post("/notes")
def upsert_note(payload: NoteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = (
        db.query(EmployeeNote)
        .filter(EmployeeNote.employee_name == payload.employee_name, EmployeeNote.year_month == payload.year_month)
        .first()
    )
    text = payload.note.strip()

    if not text:
        if row:
            db.delete(row)
            db.commit()
        return {"ok": True, "note": None}

    if row:
        row.note = text
        row.updated_by = user.username
    else:
        row = EmployeeNote(
            employee_name=payload.employee_name,
            year_month=payload.year_month,
            note=text,
            updated_by=user.username,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "note": {
            "note": row.note,
            "updated_by": row.updated_by,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        },
    }
