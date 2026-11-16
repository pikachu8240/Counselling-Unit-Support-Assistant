"""Run with:  python -m pytest -q"""
import os
import sys

import pytest
from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as app_module  # noqa: E402
from core.excel_db import log_to_excel  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    xlsx = str(tmp_path / "bookings.xlsx")
    monkeypatch.setattr(app_module, "XLSX", xlsx)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        c.get("/chat")                                   # creates session + CSRF token
        with c.session_transaction() as s:
            token = s["csrf"]
        c.token, c.xlsx = token, xlsx
        yield c


def chat(c, **body):
    return c.post("/api/chat", json=body, headers={"X-CSRF-Token": c.token}).get_json()


def all_cells(path):
    wb = load_workbook(path)
    return [str(v) for ws in wb for row in ws.iter_rows(values_only=True) for v in row if v is not None]


def test_every_page_has_emergency_banner(client):
    for url in ["/", "/chat", "/awareness", "/awareness/exam-stress", "/privacy", "/talk-to-a-person", "/staff/login"]:
        html = client.get(url).get_data(as_text=True)
        assert "16328" in html and "Talk to a person" in html, url


def test_crisis_path_arabic_and_english(client):
    r = chat(client, message="مش عايز أعيش خلاص")
    assert r["type"] == "crisis" and any(c["value"] == "16328" for c in r["contacts"])
    # normal conversation stays stopped until the student closes the crisis panel
    r = chat(client, message="الوحدة بتفتح امتى")
    assert r["type"] == "crisis"
    client.post("/api/crisis/close", json={}, headers={"X-CSRF-Token": client.token})
    assert chat(client, message="الوحدة بتفتح امتى")["type"] == "answer"
    assert chat(client, message="I want to end my life")["type"] == "crisis"


def test_emergency_button(client):
    assert chat(client, action="crisis")["type"] == "crisis"


def test_booking_flow_and_privacy(client):
    secret_text = "قلقان جدا من امتحان الكالكولاس"
    r = chat(client, message="عايز أحجز جلسة")
    assert r["type"] == "booking"
    chat(client, message=secret_text)
    day = app_module.booking_days()[0]["value"]
    r = client.post("/api/book", json={"day": day, "time": "11:00", "method": "whatsapp",
                                       "contact": "0101 234 5678"},
                    headers={"X-CSRF-Token": client.token}).get_json()
    assert r["ok"] and r["booking_id"].startswith("BK-")
    cells = all_cells(client.xlsx)
    assert r["booking_id"] in cells and "01012345678" in cells
    assert secret_text not in cells and "عايز أحجز جلسة" not in cells   # no chat text stored


def test_booking_validation(client):
    r = client.post("/api/book", json={"day": "2000-01-01", "time": "03:00", "method": "phone", "contact": "123"},
                    headers={"X-CSRF-Token": client.token})
    assert r.status_code == 400
    assert set(r.get_json()["errors"]) >= {"day", "time", "contact"}


def test_csrf_required(client):
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 400


def test_log_to_excel_refuses_extra_fields(tmp_path):
    with pytest.raises(ValueError):
        log_to_excel(str(tmp_path / "x.xlsx"), "Bookings", {"booking_id": "1", "name": "Ahmed"})


def test_stats_are_totals_only(tmp_path):
    p = str(tmp_path / "x.xlsx")
    for _ in range(3):
        log_to_excel(p, "Stats", {"intent": "services"})
    rows = list(load_workbook(p)["Stats"].iter_rows(min_row=2, values_only=True))
    assert len(rows) == 1 and rows[0][1:] == ("services", 3)


def test_staff_requires_login(client):
    assert client.get("/staff").status_code == 302
    r = client.post("/staff/login", data={"username": "staff", "password": "change-me-now", "csrf": client.token})
    assert r.status_code == 302
    assert client.get("/staff").status_code == 200
    assert client.get("/staff/evaluation").status_code == 200
    assert client.get("/staff/chart/intents.png").status_code == 200


def test_ai_test_bench(client):
    client.post("/staff/login", data={"username": "staff", "password": "change-me-now", "csrf": client.token})
    client.get("/staff/try")                     # login resets the session, so get a fresh form token
    with client.session_transaction() as s:
        client.token = s["csrf"]
    r = client.post("/staff/try", data={"message": "وزعت حاجاتي على صحابي", "csrf": client.token})
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "القرار: أزمة" in html
    r = client.post("/staff/try", data={"message": "الوحدة بتفتح امتى", "csrf": client.token})
    assert "القرار: services" in r.get_data(as_text=True)
