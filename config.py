"""Central configuration for the Counselling Unit Support Assistant.

Everything the counselling unit may want to change (contacts, staff login,
file paths) lives here. Values can be overridden with environment variables
so that secrets never have to be written into the code.
"""
import os
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- security
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
STAFF_USERNAME = os.environ.get("STAFF_USERNAME", "staff")
# Set STAFF_PASSWORD_HASH in production (see README). Default password: change-me-now
STAFF_PASSWORD_HASH = os.environ.get(
    "STAFF_PASSWORD_HASH", generate_password_hash("change-me-now")
)

# ---------------------------------------------------------------- unit contacts
# TODO(unit): replace the placeholders below with the unit's real contacts.
UNIT = {
    "name_ar": "وحدة الإرشاد النفسي والتوجيه – كلية الهندسة",
    "name_en": "Counselling & Guidance Unit – Faculty of Engineering",
    "phone": "013-0000000",          # placeholder
    "whatsapp": "01000000000",       # placeholder
    "email": "counselling@example.edu.eg",  # placeholder
    "location_ar": "المبنى الإداري – الدور الأول – غرفة 105",  # placeholder
    "location_en": "Administration building – 1st floor – room 105",
    "hours_ar": "من الأحد إلى الخميس، 9 صباحًا – 3 عصرًا",
    "hours_en": "Sunday to Thursday, 9 am – 3 pm",
}
NATIONAL_HOTLINE = "16328"   # national mental-health hotline (as given in the brief)

# ---------------------------------------------------------------- files
EXCEL_PATH = os.path.join(BASE_DIR, "instance", "bookings.xlsx")
MODEL_PATH = os.path.join(BASE_DIR, "models", "intent_model.joblib")
KEYWORDS_PATH = os.path.join(BASE_DIR, "data", "crisis_keywords.txt")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# ---------------------------------------------------------------- booking options
BOOKING_TIMES = ["10:00", "11:00", "12:00", "13:00", "14:00"]
WORKING_DAYS = {6, 0, 1, 2, 3}   # Python weekday(): Sun=6, Mon=0 ... Thu=3
BOOKING_DAYS_AHEAD = 14
CONTACT_METHODS = {
    "phone": ("مكالمة تليفون", "Phone call"),
    "whatsapp": ("واتساب", "WhatsApp"),
    "email": ("بريد إلكتروني", "Email"),
}

# If the model's top probability is below this, the assistant shows the menu
# instead of guessing (never affects the crisis check).
LOW_CONFIDENCE = 0.40
