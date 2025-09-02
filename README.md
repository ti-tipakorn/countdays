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

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Pip packages:
  ```bash
  pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
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

## ⚠️ Notes

- For `.ics` export, events use proper RFC 5545 formatting (CRLF endings, UID, DTSTAMP).  
- Recurrence is supported with `RRULE`. Example: `FREQ=YEARLY;COUNT=3`.  
- When using Google Calendar, you must have API enabled in your Google Cloud project.  

---

## 👨‍💻 Author

Coded by **ChatGPT (OpenAI)**.  
Customized, improved, and explained for practical use.

---

## 📜 License

MIT License. Free for personal and commercial use. Attribution appreciated.
