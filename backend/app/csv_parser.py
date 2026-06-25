"""Parses the wide-format 'Variable Pay - MMM YY.csv' export.

The export has three side-by-side sections — Estimation, Approval, Delivery —
each with its own "Timestamp" header cell. Column positions AND the header
row itself drift between monthly exports (extra blank/duplicate columns,
and in some exports the Approval section's header row sits one row lower
than Estimation/Delivery's). Each section is therefore located independently
by finding its own "Timestamp" header cell, then reading its field columns
from that same row, then reading its data starting the row immediately
below ITS OWN header — not a shared "row 2" offset for every section.
"""
import csv
import io
import re
from typing import Optional

HEADER_SCAN_ROWS = 6  # how many leading rows to scan for section header cells


def _cell(row: list[str], idx: Optional[int]) -> str:
    if idx is None or idx >= len(row) or row[idx] is None:
        return ""
    return row[idx].strip()


def _split_names(s: str) -> list[str]:
    return [n.strip() for n in re.split(r"[,\n]+", s) if n.strip()]


def _to_float(s: str) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def _find(header_row: list[str], start: int, end: int, *needles: str, exclude: str = None) -> Optional[int]:
    """First column index in [start, end) whose header contains all needles (case-insensitive)."""
    for i in range(start, min(end, len(header_row))):
        h = header_row[i].lower()
        if exclude and exclude in h:
            continue
        if all(n in h for n in needles):
            return i
    return None


def _locate_sections(rows: list[list[str]]) -> list[tuple[int, int]]:
    """Find each section's (header_row, timestamp_col), ordered left-to-right by column."""
    hits = []
    for r in range(min(HEADER_SCAN_ROWS, len(rows))):
        for c, val in enumerate(rows[r]):
            if val.strip().lower() == "timestamp":
                hits.append((r, c))
    hits.sort(key=lambda rc: rc[1])  # order by column ascending
    if len(hits) < 3:
        raise ValueError(f"Expected 3 'Timestamp' header cells (Estimation/Approval/Delivery), found {len(hits)}")
    return hits[:3]


def parse_variable_pay_csv(text: str) -> dict:
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if any(c.strip() for c in row)]

    (est_row, est_ts), (app_row, app_ts), (del_row, del_ts) = _locate_sections(rows)
    row_width = max(len(r) for r in rows)

    est_header, app_header, del_header = rows[est_row], rows[app_row], rows[del_row]
    est_prj = _find(est_header, est_ts, app_ts, "project")
    est_est = _find(est_header, est_ts, app_ts, "estimator")
    est_mgr = _find(est_header, est_ts, app_ts, "manager")

    app_prj = _find(app_header, app_ts, del_ts, "project")
    app_est = _find(app_header, app_ts, del_ts, "estimator")
    app_mgr = _find(app_header, app_ts, del_ts, "manager")

    del_prj = _find(del_header, del_ts, row_width, "project")
    del_mgr = _find(del_header, del_ts, row_width, "manager")
    del_fb  = _find(del_header, del_ts, row_width, "feedback")
    del_dev = _find(del_header, del_ts, row_width, "developer")
    del_act = _find(del_header, del_ts, row_width, "hours", "develo")
    del_app = _find(del_header, del_ts, row_width, "hours", exclude="develo")

    estimations, approvals, deliveries = [], [], []

    for r in rows[est_row + 1:]:
        e_ts, e_prj, e_est, e_mgr = _cell(r, est_ts), _cell(r, est_prj), _cell(r, est_est), _cell(r, est_mgr)
        if e_ts and e_prj and e_est:
            estimations.append({
                "ts": e_ts, "project": e_prj,
                "estimators": _split_names(e_est), "manager": e_mgr,
            })

    for r in rows[app_row + 1:]:
        a_ts, a_prj, a_est, a_mgr = _cell(r, app_ts), _cell(r, app_prj), _cell(r, app_est), _cell(r, app_mgr)
        if a_ts and a_prj and a_est:
            approvals.append({
                "ts": a_ts, "project": a_prj,
                "estimators": _split_names(a_est), "manager": a_mgr,
            })

    for r in rows[del_row + 1:]:
        d_ts, d_prj, d_mgr = _cell(r, del_ts), _cell(r, del_prj), _cell(r, del_mgr)
        d_fb, d_dev = _cell(r, del_fb), _cell(r, del_dev)
        d_act, d_app = _to_float(_cell(r, del_act)), _to_float(_cell(r, del_app))
        if d_ts and d_prj and d_dev:
            deliveries.append({
                "ts": d_ts, "project": d_prj, "manager": d_mgr, "feedback": d_fb,
                "developers": _split_names(d_dev),
                "actualHours": d_act, "approvedHours": d_app,
            })

    return {"estimations": estimations, "approvals": approvals, "deliveries": deliveries}


def detect_year_month(parsed: dict) -> Optional[str]:
    first = (
        (parsed["estimations"][0] if parsed["estimations"] else None)
        or (parsed["approvals"][0] if parsed["approvals"] else None)
        or (parsed["deliveries"][0] if parsed["deliveries"] else None)
    )
    if not first:
        return None
    return first["ts"][:7]
