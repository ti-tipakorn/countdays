# 📅 Date Counter & ICS Maker

A cross-platform Python GUI app for date calculations and calendar event creation.  
It supports `.ics` file export (for Outlook/Apple/Google Calendar import) and **direct Google Calendar insertion** using OAuth.

---

## ✨ Features

- **Three calculation modes**:
  1. **Count days until a given end date**  
     Enter an **end date**, get the number of days between today (or a custom start date) and the end date.
  2. **Add days to a start date → get end date**  
     Enter a number of days (e.g. `121`), and it calculates the resulting end date.
  3. **Subtract days from an end date → get start date**  
     Enter an **end date** and how many days to subtract, and it calculates the start date.
- **.ics event generation**  
  - All-day or timed events.  
  - Up to 3 reminders (VALARMs).  
  - Supports recurrence rules (RRULE: daily, weekly, monthly, yearly, or custom).  
- **Google Calendar integration**  
  - Optional insert into your primary Google Calendar.  
  - Requires a Google Cloud OAuth client (`credentials.json`).  
- **GUI** built with `tkinter` (no external GUI libraries required).  
- Supports multiple date formats (`MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`).  
- Timezone-aware (defaults to `America/New_York`).  
  - Dropdown of common IANA timezones (e.g. `Asia/Bangkok`, `Europe/London`).  
  - "Custom…" option lets you enter any valid timezone manually.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Pip packages:
  ```bash
  pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib tzdata
  ```

### Clone & Run
```bash
git clone https://github.com/yourusername/date-counter-ics.git
cd date-counter-ics
python main.py
```

---

## 🔑 Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).  
2. Create a new project.  
3. Enable **Google Calendar API**.  
4. Create **OAuth Client ID** credentials (type: *Desktop app*).  
5. Download as `credentials.json` and place it in the same folder as `main.py`.  
6. First run → a browser window opens → log in and authorize.  
   - A `token.pickle` will be saved locally so you don’t need to log in every time.  

---

## 🖼️ Usage Guide

1. Choose a **mode**:
   - **Mode 1:** Count days until an end date.  
   - **Mode 2:** Add days to a start date → get end date.  
   - **Mode 3:** Subtract days from an end date → get start date.  
2. Optionally set a custom **start date** (instead of today).  
3. Enter event details (title, all-day/timed, reminders, recurrence).  
4. Press **Compute**.  
   - Results appear in the output box.  
   - If enabled, a `.ics` file is prepared and/or event inserted into Google Calendar.  

---

## 📝 Example

- Start = 09/02/2025  
- Days = 121  
- Mode 2 (Add days to start → end date)  
- → Result = **01/01/2026**

Generate `.ics` file → save → double-click to add to your default calendar.  
Or check **Google Calendar insert** → the event is created instantly in your calendar.

---

## 📆 Recurrence Rules (RRULE)

The app supports **recurring events** using the [iCalendar RRULE standard (RFC 5545)](https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html).  
This means you can repeat an event daily, weekly, monthly, yearly, or even define a custom pattern.

### 🔧 Built-in options
In the GUI, you can quickly choose:

- **Daily** – repeats every N days  
- **Weekly** – repeats every N weeks  
- **Monthly** – repeats every N months  
- **Yearly** – repeats every N years  
- **Custom…** – enter your own RRULE string  

You can also add:
- **Interval** → e.g. every 2 weeks (`INTERVAL=2`)  
- **Count** → e.g. repeat 5 times only (`COUNT=5`)  
- **Until** → stop at a specific date (`UNTIL=20251231T235959Z`)  

### 🖊 Custom RRULE syntax
A custom RRULE must start with one or more `KEY=VALUE` pairs, separated by `;`.

Common parts:
- `FREQ` → frequency (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`)
- `INTERVAL` → step size (default = 1)
- `BYDAY` → pick specific weekdays (`MO,TU,FR`)
- `BYMONTHDAY` → pick specific days of the month (`15`, `1,-1`)
- `BYMONTH` → pick months (`1`=Jan, `12`=Dec)
- `COUNT` → stop after N repeats
- `UNTIL` → stop at a specific date/time (in UTC, `YYYYMMDDTHHMMSSZ`)

### 📋 Examples

**1. Every day for 10 days**
```
RRULE:FREQ=DAILY;COUNT=10
```

**2. Every other day (forever)**
```
RRULE:FREQ=DAILY;INTERVAL=2
```

**3. Every Monday and Wednesday for 5 weeks**
```
RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=10
```

**4. Every month on the 15th, 5 occurrences**
```
RRULE:FREQ=MONTHLY;BYMONTHDAY=15;COUNT=5
```

**5. Every year on January 1st, forever**
```
RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1
```

**6. Every last Friday of the month, until end of 2026**
```
RRULE:FREQ=MONTHLY;BYDAY=-1FR;UNTIL=20261231T235959Z
```

**7. Every weekday (Mon–Fri) for 20 occurrences**
```
RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;COUNT=20
```

**8. Every 2 years on Feb 29 (leap years only)**
```
RRULE:FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29;INTERVAL=4
```

### ⚠ Notes
- `UNTIL` must be in **UTC time** (`Z` at the end).  
- If you enter `RRULE:` at the start, the app strips it automatically — you can enter either:
  - `RRULE:FREQ=DAILY;COUNT=5`
  - or just `FREQ=DAILY;COUNT=5`
- Not all calendar apps support *all* RRULEs (Google Calendar supports most common ones).

---

## 👨‍💻 Author

Coded by **ChatGPT (OpenAI)**.  
Customized, improved, and explained for practical use.

---

## 📜 License

MIT License. Free for personal and commercial use. Attribution appreciated.
