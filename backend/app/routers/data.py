import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..csv_parser import detect_year_month, parse_variable_pay_csv
from ..deps import get_current_user, get_db
from ..models import MonthData, User
from ..records import merge_upload, tag_parsed
from ..schemas import MonthSummary, UploadResult

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/months", response_model=list[MonthSummary])
def list_months(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(MonthData).order_by(MonthData.year_month).all()
    return [
        MonthSummary(year_month=r.year_month, source_filename=r.source_filename, uploaded_by=r.uploaded_by)
        for r in rows
    ]


@router.get("/data")
def get_data(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(MonthData).order_by(MonthData.year_month).all()
    return {r.year_month: json.loads(r.data_json) for r in rows}


@router.post("/upload", response_model=list[UploadResult])
async def upload_csvs(
    files: list[UploadFile],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    results = []
    for file in files:
        try:
            raw = await file.read()
            text = raw.decode("utf-8-sig")
            parsed = parse_variable_pay_csv(text)
            ym = detect_year_month(parsed)
            if not ym:
                raise ValueError("No timestamps found in file")

            tagged = tag_parsed(parsed)
            existing = db.query(MonthData).filter(MonthData.year_month == ym).first()
            existing_blob = json.loads(existing.data_json) if existing else None
            merged = merge_upload(existing_blob, tagged)

            if existing:
                existing.data_json = json.dumps(merged)
                existing.source_filename = file.filename
                existing.uploaded_by = user.username
            else:
                db.add(MonthData(
                    year_month=ym,
                    source_filename=file.filename,
                    data_json=json.dumps(merged),
                    uploaded_by=user.username,
                ))
            db.commit()
            results.append(UploadResult(filename=file.filename, year_month=ym, ok=True))
        except Exception as e:
            db.rollback()
            results.append(UploadResult(filename=file.filename, year_month=None, ok=False, error=str(e)))
    return results


@router.delete("/months/{year_month}")
def delete_month(year_month: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    row = db.query(MonthData).filter(MonthData.year_month == year_month).first()
    if not row:
        raise HTTPException(status_code=404, detail="Month not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
