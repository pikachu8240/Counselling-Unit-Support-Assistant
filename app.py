"""Counselling Unit Support Assistant — Flask application.

Run:   python app.py      then open http://127.0.0.1:5000
(train the model first with:  python train.py  &&  python evaluate.py)

Privacy by design:
  * chat messages are analysed in memory and never written anywhere
  * no names are asked or stored; only the fields in core/excel_db.SCHEMA
  * the crisis check runs FIRST on every message
"""
import io
import json
import os
import re
import secrets
from datetime import date, timedelta
from functools import wraps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.security import check_password_hash

import config
from core import content
from core.excel_db import (BOOKING_STATUSES, log_to_excel, new_booking_id,
                           read_sheet)
from core.model import Assistant
from core.text_clean import detect_language

app = Flask(__name__)
app.config.update(SECRET_KEY=config.SECRET_KEY,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(hours=2))

assistant = Assistant(config.MODEL_PATH, config.KEYWORDS_PATH, config.LOW_CONFIDENCE)
XLSX = config.EXCEL_PATH
AR_DAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


# ------------------------------------------------------------------ helpers
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def check_csrf():
    sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf")
    if not sent or sent != session.get("csrf"):
        abort(400, "Invalid form token – please reload the page.")


app.jinja_env.globals.update(csrf_token=csrf_token, UNIT=config.UNIT,
                             HOTLINE=config.NATIONAL_HOTLINE)


def staff_required(view):
    @wraps(view)
    def wrapper(*a, **kw):
        if not session.get("staff"):
            return redirect(url_for("staff_login", next=request.path))
        return view(*a, **kw)
    return wrapper


def safe_log(sheet, data, **kw):
    """Logging must never break the conversation (e.g. file open in Excel)."""
    try:
        log_to_excel(XLSX, sheet, data, **kw)
        return True
    except PermissionError:
        app.logger.warning("bookings.xlsx is locked (open in Excel?) – %s not logged", sheet)
        return False


def booking_days():
    days, d = [], date.today() + timedelta(days=1)
    while len(days) < 8 and (d - date.today()).days <= config.BOOKING_DAYS_AHEAD:
        if d.weekday() in config.WORKING_DAYS:
            days.append({"value": d.isoformat(),
                         "label_ar": f"{AR_DAYS[d.weekday()]} {d.day}/{d.month}",
                         "label_en": d.strftime("%a %d %b")})
        d += timedelta(days=1)
    return days


def crisis_payload(lang):
    return {"type": "crisis", "intent": "crisis", "lang": lang,
            "html": content.CRISIS[lang],
            "contacts": [{"label": c[f"label_{lang}"], "value": c["value"], "href": c["href"]}
                         for c in content.CRISIS_CONTACTS]}


# ------------------------------------------------------------------ visits
PUBLIC_PAGES = {"index", "chat", "awareness", "awareness_article", "privacy", "talk"}


@app.after_request
def record_visit(resp):
    if (request.method == "GET" and request.endpoint in PUBLIC_PAGES
            and resp.status_code == 200):
        safe_log("Visits", {"page": request.path, "date": date.today().isoformat()})
    return resp


# ------------------------------------------------------------------ public pages
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat")
def chat():
    return render_template("chat.html", intro=content.INTRO, days=booking_days(),
                           times=config.BOOKING_TIMES, methods=config.CONTACT_METHODS,
                           in_crisis=session.get("crisis", False))


@app.route("/awareness")
def awareness():
    return render_template("awareness.html", articles=content.AWARENESS)


@app.route("/awareness/<slug>")
def awareness_article(slug):
    art = content.awareness_by_slug(slug)
    if not art:
        abort(404)
    return render_template("article.html", a=art)


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/talk-to-a-person")
def talk():
    return render_template("talk.html", contacts=content.CRISIS_CONTACTS)


# ------------------------------------------------------------------ chat API
QUICK_ACTIONS = {"services", "booking", "stress", "crisis"}


@app.post("/api/chat")
def api_chat():
    check_csrf()
    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").strip()
    message = (body.get("message") or "").strip()[:1000]
    lang = detect_language(message) if message else session.get("lang", "ar")
    session["lang"] = lang

    # 1) quick-action buttons
    if action in QUICK_ACTIONS:
        intent = action
        if intent == "crisis":
            session["crisis"] = True
            safe_log("Stats", {"intent": "crisis"})
            return jsonify(crisis_payload(lang))
    elif message:
        # 2) CRISIS CHECK FIRST — two layers (keywords OR model)
        result = assistant.analyze(message)
        message = None                               # the text is not kept beyond this point
        if result["is_crisis"]:
            session["crisis"] = True
            safe_log("Stats", {"intent": "crisis"})
            return jsonify(crisis_payload(lang))
        # 3) while a crisis is open the normal conversation stays stopped
        if session.get("crisis"):
            return jsonify(crisis_payload(lang) | {"still_open": True})
        intent = "unsure" if result.get("low_confidence") else result["intent"]
    else:
        return jsonify({"type": "answer", "intent": "empty", "html": content.RESPONSES["unsure"][lang]})

    if session.get("crisis"):
        return jsonify(crisis_payload(lang) | {"still_open": True})

    safe_log("Stats", {"intent": intent if intent != "unsure" else "other"})
    reply = {"type": "booking" if intent == "booking" else "answer",
             "intent": intent, "lang": lang, "html": content.RESPONSES[intent][lang]}
    if intent in ("unsure", "other"):
        reply["show_menu"] = True
    if intent == "stress":
        reply["offer_booking"] = True
    return jsonify(reply)


@app.post("/api/crisis/close")
def api_crisis_close():
    """Student confirms they are safe / have reached someone."""
    check_csrf()
    session.pop("crisis", None)
    return jsonify({"ok": True})


PHONE_RE = re.compile(r"^01[0125]\d{8}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[A-Za-z]{2,}$")


@app.post("/api/book")
def api_book():
    check_csrf()
    b = request.get_json(silent=True) or {}
    lang = session.get("lang", "ar")
    day, time_, method = b.get("day", ""), b.get("time", ""), b.get("method", "")
    contact = re.sub(r"[\s\-]", "", b.get("contact", "")) if method != "email" else b.get("contact", "").strip()
    contact = contact.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))

    errors = []
    if day not in {d["value"] for d in booking_days()}:
        errors.append("day")
    if time_ not in config.BOOKING_TIMES:
        errors.append("time")
    if method not in config.CONTACT_METHODS:
        errors.append("method")
    elif method == "email" and not EMAIL_RE.match(contact):
        errors.append("contact")
    elif method in ("phone", "whatsapp") and not PHONE_RE.match(contact):
        errors.append("contact")
    if session.get("bookings", 0) >= 3:
        errors.append("limit")
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    bid = new_booking_id()
    ok = safe_log("Bookings", {"booking_id": bid, "created_at": date.today().isoformat(),
                               "preferred_day": day, "preferred_time": time_,
                               "contact_method": method, "contact": contact, "status": "new"})
    if not ok:
        return jsonify({"ok": False, "errors": ["busy"]}), 503
    session["bookings"] = session.get("bookings", 0) + 1
    m_ar, m_en = config.CONTACT_METHODS[method]
    msg = {"ar": f"✅ تم استلام طلب الحجز. رقم الحجز: <b>{bid}</b><br>"
                 f"الوحدة هتتواصل معاك عن طريق ({m_ar}) لتأكيد الميعاد يوم {day} الساعة {time_}.<br>"
                 "احتفظ برقم الحجز لو حبيت تغيّر أو تلغي.",
           "en": f"✅ Booking request received. Booking ID: <b>{bid}</b><br>"
                 f"The unit will contact you by {m_en} to confirm {day} at {time_}.<br>"
                 "Keep the booking ID if you want to change or cancel."}
    return jsonify({"ok": True, "booking_id": bid, "html": msg[lang]})


@app.post("/api/feedback")
def api_feedback():
    check_csrf()
    helpful = (request.get_json(silent=True) or {}).get("helpful")
    if helpful not in ("yes", "no"):
        abort(400)
    safe_log("Feedback", {"date": date.today().isoformat(), "helpful": helpful})
    return jsonify({"ok": True})


# ------------------------------------------------------------------ staff area
@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    error = None
    if request.method == "POST":
        check_csrf()
        if (request.form.get("username") == config.STAFF_USERNAME and
                check_password_hash(config.STAFF_PASSWORD_HASH, request.form.get("password", ""))):
            session.clear()
            session["staff"] = True
            session.permanent = True
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/staff") else url_for("staff_dashboard"))
        error = "اسم المستخدم أو كلمة المرور غير صحيحة"
    return render_template("staff/login.html", error=error)


@app.route("/staff/logout")
def staff_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/staff")
@staff_required
def staff_dashboard():
    bookings = read_sheet(XLSX, "Bookings")
    stats = read_sheet(XLSX, "Stats")
    visits = read_sheet(XLSX, "Visits")
    feedback = read_sheet(XLSX, "Feedback")
    if not stats.empty:
        stats["count"] = pd.to_numeric(stats["count"], errors="coerce").fillna(0).astype(int)
    totals = stats.groupby("intent")["count"].sum().to_dict() if not stats.empty else {}
    kpi = {
        "bookings_new": int((bookings["status"] == "new").sum()) if not bookings.empty else 0,
        "bookings_total": len(bookings),
        "messages": int(sum(totals.values())),
        "crisis": int(totals.get("crisis", 0)),
        "visits": len(visits),
        "helpful": (f"{(feedback['helpful'] == 'yes').mean():.0%}" if not feedback.empty else "–"),
    }
    by_page = visits["page"].value_counts().to_dict() if not visits.empty else {}
    return render_template("staff/dashboard.html",
                           bookings=bookings.iloc[::-1].to_dict("records"),
                           totals=totals, kpi=kpi, by_page=by_page,
                           statuses=BOOKING_STATUSES, methods=config.CONTACT_METHODS)


@app.post("/staff/booking/<bid>/status")
@staff_required
def staff_booking_status(bid):
    check_csrf()
    status = request.form.get("status")
    if status not in BOOKING_STATUSES:
        abort(400)
    log_to_excel(XLSX, "Bookings", {"booking_id": bid, "status": status}, key="booking_id")
    return redirect(url_for("staff_dashboard") + "#bookings")


CHART_COLORS = {"booking": "#2563eb", "services": "#0d9488", "stress": "#d97706",
                "crisis": "#dc2626", "other": "#6b7280"}


@app.route("/staff/chart/<name>.png")
@staff_required
def staff_chart(name):
    fig, ax = plt.subplots(figsize=(6.4, 3.2), dpi=120)
    if name == "intents":
        stats = read_sheet(XLSX, "Stats")
        if stats.empty:
            ax.text(.5, .5, "No data yet", ha="center", va="center"); ax.axis("off")
        else:
            stats["count"] = pd.to_numeric(stats["count"], errors="coerce").fillna(0)
            stats["date"] = pd.to_datetime(stats["date"])
            last = stats[stats["date"] >= stats["date"].max() - pd.Timedelta(days=13)]
            piv = last.pivot_table(index="date", columns="intent", values="count", aggfunc="sum").fillna(0)
            bottom = None
            for intent in [i for i in CHART_COLORS if i in piv.columns]:
                ax.bar(piv.index.strftime("%d/%m"), piv[intent], bottom=bottom,
                       color=CHART_COLORS[intent], label=intent, width=.7)
                bottom = piv[intent] if bottom is None else bottom + piv[intent]
            ax.legend(frameon=False, fontsize=8, ncol=5, loc="upper left", bbox_to_anchor=(0, 1.18))
            ax.set_ylabel("messages / day")
    elif name == "visits":
        v = read_sheet(XLSX, "Visits")
        if v.empty:
            ax.text(.5, .5, "No data yet", ha="center", va="center"); ax.axis("off")
        else:
            c = v["page"].value_counts().head(8)[::-1]
            ax.barh(c.index, c.values, color="#2563eb")
            ax.set_xlabel("visits")
    else:
        abort(404)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig); buf.seek(0)
    return send_file(buf, mimetype="image/png", max_age=0)


@app.route("/staff/evaluation")
@staff_required
def staff_evaluation():
    def load(name):
        p = os.path.join(config.REPORTS_DIR, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    trick_p = os.path.join(config.REPORTS_DIR, "trick_results.csv")
    trick = pd.read_csv(trick_p, encoding="utf-8-sig").fillna("").to_dict("records") if os.path.exists(trick_p) else []
    return render_template("staff/evaluation.html", m=load("metrics.json"),
                           sel=load("model_selection.json"), trick=trick)


@app.route("/staff/try", methods=["GET", "POST"])
@staff_required
def staff_try():
    """AI test bench: type a message, see both crisis layers and all class
    probabilities. Nothing typed here is stored or counted in Stats."""
    result, text = None, ""
    if request.method == "POST":
        check_csrf()
        text = (request.form.get("message") or "").strip()[:1000]
        if text:
            result = assistant.explain(text)
    examples = ["قلقان جدا من الميدتيرم", "عايز احجز جلسة يوم الاحد", "الوحدة بتفتح امتى",
                "الامتحان ده هيموتني", "وزعت حاجاتي على صحابي", "I want to book a session"]
    return render_template("staff/try.html", result=result, text=text, examples=examples)


@app.route("/staff/report/confusion_matrix.png")
@staff_required
def staff_confusion():
    return send_file(os.path.join(config.REPORTS_DIR, "confusion_matrix.png"), max_age=0)


@app.errorhandler(404)
def not_found(e):
    return render_template("message.html", title="الصفحة غير موجودة", text="الرابط ده مش موجود."), 404


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="127.0.0.1", port=5000)
