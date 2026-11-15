# Privacy statement: Counselling Unit Support Assistant
*(one page, also shown to students at `/privacy`)*

**Purpose.** The assistant helps students learn about the counselling unit and book a session without embarrassment.
It is a computer program, not a therapist. It never diagnoses and never gives treatment advice.

## What we store, and why
All data is kept in **one Excel file, `bookings.xlsx`, on the counselling unit's own computer** (`instance/` folder).
Nothing is sent to an external server.

| Sheet | Fields | Why |
|---|---|---|
| **Bookings** | booking ID, time of request, preferred day, preferred time, contact method, contact (phone or email), status | So the unit can contact the student and confirm the session |
| **Stats** | date, intent, count (daily totals only) | So the unit knows what students need (for example, how many asked about exam stress this week) |
| **Visits** | page, date | To see which pages are useful |
| **Feedback** | date, helpful yes/no | To improve the answers |

## What we never store
- **Names.** The assistant never asks for a name.
- **Chat text.** Every message is analysed in memory and then discarded. It is not written to the Excel file, logs or the browser.
- IP addresses, device information or location.
- Any link between a chat and a booking.

These rules are enforced in code. `log_to_excel()` refuses any field that is not in the schema above, and an automated
test checks that chat text never appears in the file.

## How messages are analysed
Each message is checked **first** for signs of crisis (a keyword list written by the unit's specialists, plus a
machine-learning model) and then classified into one of five intents. If a crisis is detected, the assistant immediately
shows the national hotline **16328**, the unit's contacts and emergency number 123.

## Who can see the data
Only authorised unit staff, through a password-protected staff page. It shows bookings and anonymous counts only.

## Retention and deletion
Completed or cancelled bookings should be deleted every 6 months (a recommendation for the unit to confirm).
A student can ask the unit to delete their booking by quoting the booking ID.

## Limits of confidentiality
Counsellors keep sessions confidential except when there is a clear risk to the student's life or someone else's.

*Contact: the counselling unit. See the contacts on every page.*
