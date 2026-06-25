from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonthSummary(BaseModel):
    year_month: str
    source_filename: str | None
    uploaded_by: str | None


class UploadResult(BaseModel):
    filename: str
    year_month: str | None
    ok: bool
    error: str | None = None


class NoteIn(BaseModel):
    employee_name: str
    year_month: str
    note: str


class NoteOut(BaseModel):
    employee_name: str
    year_month: str
    note: str
    updated_by: str | None
    updated_at: str | None
