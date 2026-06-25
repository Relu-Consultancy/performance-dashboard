from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class MonthData(Base):
    __tablename__ = "month_data"

    id = Column(Integer, primary_key=True, index=True)
    year_month = Column(String, unique=True, index=True, nullable=False)  # "YYYY-MM"
    source_filename = Column(String, nullable=True)
    data_json = Column(Text, nullable=False)  # {estimations:[], approvals:[], deliveries:[]}
    uploaded_by = Column(String, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())


class EmployeeNote(Base):
    __tablename__ = "employee_notes"
    __table_args__ = (UniqueConstraint("employee_name", "year_month", name="uq_employee_month_note"),)

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, index=True, nullable=False)
    year_month = Column(String, index=True, nullable=False)  # "YYYY-MM"
    note = Column(Text, nullable=False)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
