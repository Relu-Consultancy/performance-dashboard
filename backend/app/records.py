"""Shared helpers for record-level bookkeeping (id/source/edited tagging,
re-upload merge logic) used by both the CSV upload endpoint and the manual
data-entry CRUD endpoints. Records live inside MonthData.data_json, keyed
by "estimations" / "approvals" / "deliveries".
"""
import uuid
from typing import Optional

RECORD_TYPES = ("estimations", "approvals", "deliveries")

REQUIRED_FIELDS = {
    "estimations": ["ts", "project", "estimators", "manager"],
    "approvals": ["ts", "project", "estimators", "manager"],
    "deliveries": ["ts", "project", "manager", "feedback", "developers", "actualHours", "approvedHours"],
}


def new_id() -> str:
    return uuid.uuid4().hex


def blank_blob() -> dict:
    return {rtype: [] for rtype in RECORD_TYPES}


def tag_parsed(parsed: dict) -> dict:
    """Stamp every freshly-parsed CSV row with id/source/edited bookkeeping fields."""
    tagged = {}
    for rtype in RECORD_TYPES:
        rows = []
        for r in parsed.get(rtype, []):
            row = dict(r)
            row["id"] = new_id()
            row["source"] = "csv"
            row["edited"] = False
            rows.append(row)
        tagged[rtype] = rows
    return tagged


def _natural_key(row: dict) -> tuple:
    return (row.get("ts", ""), row.get("project", ""))


def _merge_rows(existing_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    manual_rows = [r for r in existing_rows if r.get("source") == "manual"]
    existing_csv_by_key = {_natural_key(r): r for r in existing_rows if r.get("source") != "manual"}

    merged, seen_keys = [], set()
    for new_row in new_rows:
        key = _natural_key(new_row)
        seen_keys.add(key)
        old = existing_csv_by_key.get(key)
        # If this row was previously manually corrected, keep the correction instead of the fresh CSV value
        merged.append(old if (old and old.get("edited")) else new_row)

    for key, old in existing_csv_by_key.items():
        if old.get("edited") and key not in seen_keys:
            merged.append(old)  # user fixed a row the new CSV no longer contains — keep the fix

    return merged + manual_rows


def merge_upload(existing: Optional[dict], new_tagged: dict) -> dict:
    """Combine a freshly-parsed (and tagged) CSV with whatever's already stored for that
    month, preserving any manually-added rows and any CSV rows the user has hand-edited.
    """
    existing = existing or {}
    return {
        rtype: _merge_rows(existing.get(rtype, []), new_tagged.get(rtype, []))
        for rtype in RECORD_TYPES
    }
