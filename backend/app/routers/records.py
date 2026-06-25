import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import MonthData, User
from ..records import RECORD_TYPES, REQUIRED_FIELDS, blank_blob, new_id

router = APIRouter(prefix="/api", tags=["records"])


def _load_blob(month: MonthData | None) -> dict:
    if month is None or not month.data_json:
        return blank_blob()
    blob = json.loads(month.data_json)
    for rtype in RECORD_TYPES:
        blob.setdefault(rtype, [])
    return blob


def _validate_rtype(rtype: str):
    if rtype not in RECORD_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown record type '{rtype}'. Must be one of {RECORD_TYPES}.")


def _validate_payload(rtype: str, payload: dict):
    missing = [f for f in REQUIRED_FIELDS[rtype] if f not in payload or payload[f] in (None, "")]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required field(s): {', '.join(missing)}")


@router.get("/records/{year_month}/{rtype}")
def list_records(
    year_month: str, rtype: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    _validate_rtype(rtype)
    month = db.query(MonthData).filter(MonthData.year_month == year_month).first()
    return _load_blob(month).get(rtype, [])


@router.post("/records/{year_month}/{rtype}")
def create_record(
    year_month: str,
    rtype: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _validate_rtype(rtype)
    _validate_payload(rtype, payload)

    month = db.query(MonthData).filter(MonthData.year_month == year_month).first()
    blob = _load_blob(month)

    record = dict(payload)
    record["id"] = new_id()
    record["source"] = "manual"
    record["edited"] = False
    blob[rtype].append(record)

    if month:
        month.data_json = json.dumps(blob)
    else:
        month = MonthData(year_month=year_month, data_json=json.dumps(blob), uploaded_by=user.username)
        db.add(month)
    db.commit()
    return record


@router.put("/records/{year_month}/{rtype}/{record_id}")
def update_record(
    year_month: str,
    rtype: str,
    record_id: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _validate_rtype(rtype)
    _validate_payload(rtype, payload)

    month = db.query(MonthData).filter(MonthData.year_month == year_month).first()
    if not month:
        raise HTTPException(status_code=404, detail="Month not found")
    blob = _load_blob(month)
    rows = blob[rtype]
    idx = next((i for i, r in enumerate(rows) if r.get("id") == record_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Record not found")

    updated = dict(payload)
    updated["id"] = record_id
    updated["source"] = rows[idx].get("source", "manual")
    updated["edited"] = True
    rows[idx] = updated
    month.data_json = json.dumps(blob)
    db.commit()
    return updated


@router.delete("/records/{year_month}/{rtype}/{record_id}")
def delete_record(
    year_month: str,
    rtype: str,
    record_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _validate_rtype(rtype)
    month = db.query(MonthData).filter(MonthData.year_month == year_month).first()
    if not month:
        raise HTTPException(status_code=404, detail="Month not found")
    blob = _load_blob(month)
    rows = blob[rtype]
    new_rows = [r for r in rows if r.get("id") != record_id]
    if len(new_rows) == len(rows):
        raise HTTPException(status_code=404, detail="Record not found")
    blob[rtype] = new_rows
    month.data_json = json.dumps(blob)
    db.commit()
    return {"ok": True}
