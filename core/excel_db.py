"""bookings.xlsx — the only place the assistant stores anything.

Sheets (exactly what the brief allows — no names, no chat text):
  Bookings : booking_id | created_at | preferred_day | preferred_time |
             contact_method | contact | status
  Stats    : date | intent | count          (daily totals only)
  Visits   : page | date                    (no IP, no user id, no time of day)
  Feedback : date | helpful                 (yes/no button, no free text)

ALL writes go through one function: log_to_excel().
The file stays on the unit's computer (instance/ folder, git-ignored).
"""
import os
import threading
from datetime import date, datetime

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

SCHEMA = {
    "Bookings": ["booking_id", "created_at", "preferred_day", "preferred_time",
                 "contact_method", "contact", "status"],
    "Stats": ["date", "intent", "count"],
    "Visits": ["page", "date"],
    "Feedback": ["date", "helpful"],
}
BOOKING_STATUSES = ["new", "confirmed", "done", "cancelled", "no_show"]
_LOCK = threading.Lock()


def _ensure(path):
    if os.path.exists(path):
        wb = load_workbook(path)
        changed = False
        for name, cols in SCHEMA.items():
            if name not in wb.sheetnames:
                ws = wb.create_sheet(name); ws.append(cols); changed = True
        if changed:
            wb.save(path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    for name, cols in SCHEMA.items():
        ws = wb.create_sheet(name)
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="1F4E79")
        for i, _ in enumerate(cols, start=1):
            ws.column_dimensions[chr(64 + i)].width = 20
    wb.save(path)


def log_to_excel(path: str, sheet: str, data: dict, key: str = None):
    """The single write function.

    * Bookings / Visits / Feedback: append `data` as a new row.
    * Bookings with key='booking_id': update the existing row (status change).
    * Stats: `data` = {'intent': ...}; increments today's count for that
      intent (a running total — individual messages are never recorded).
    Unknown fields are refused so that nothing outside the schema
    (e.g. a name or a chat message) can ever be written by mistake.
    """
    if sheet not in SCHEMA:
        raise ValueError(f"Unknown sheet {sheet}")
    cols = SCHEMA[sheet]
    extra = set(data) - set(cols)
    if extra:
        raise ValueError(f"Refusing to store fields not in the privacy schema: {extra}")

    with _LOCK:
        _ensure(path)
        wb = load_workbook(path)
        ws = wb[sheet]

        if sheet == "Stats":
            today = data.get("date") or date.today().isoformat()
            intent = data["intent"]
            for row in ws.iter_rows(min_row=2):
                if row[0].value == today and row[1].value == intent:
                    row[2].value = int(row[2].value or 0) + int(data.get("count", 1))
                    break
            else:
                ws.append([today, intent, int(data.get("count", 1))])

        elif key:
            idx = cols.index(key)
            for row in ws.iter_rows(min_row=2):
                if row[idx].value == data[key]:
                    for k, v in data.items():
                        row[cols.index(k)].value = v
                    break
            else:
                raise KeyError(f"{key}={data[key]} not found")

        else:
            ws.append([data.get(c, "") for c in cols])

        wb.save(path)


def read_sheet(path: str, sheet: str) -> pd.DataFrame:
    """Read one sheet with pandas (for the staff dashboard)."""
    with _LOCK:
        _ensure(path)
        return pd.read_excel(path, sheet_name=sheet, dtype=str).fillna("")


def new_booking_id() -> str:
    return "BK-" + datetime.now().strftime("%y%m%d") + "-" + os.urandom(2).hex().upper()
