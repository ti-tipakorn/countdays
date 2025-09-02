#!/usr/bin/env python3
"""
Date Counter & .ics Maker (with optional Google Calendar insert)

Now with **3 modes** and **Recurrence (RRULE)**:
1) End date → days between start (today by default) and end
2) Days from start → end date
3) Days before end date → start date (NEW)

Extras:
- Date picker popups (no extra packages)
- Optional TIMED events (start time + duration)
- Up to 3 device reminders embedded as VALARMs in the .ics
- Optional insert into Google Calendar

Requires (for Google only):
  pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Tested on Python 3.11+. Should work on 3.9+.
"""
from __future__ import annotations
from pathlib import Path
import uuid
import calendar as pycalendar
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone, time
try:
    from zoneinfo import ZoneInfo
except Exception:  # Python <3.9 fallback (optional)
    ZoneInfo = None  # type: ignore

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Script directory (robust against PowerShell working-dir issues)
APP_DIR = Path(__file__).resolve().parent
CRED_PATH = APP_DIR / "credentials.json"
TOKEN_PATH = APP_DIR / "token.pickle"

# ------------------------------ Utilities ------------------------------ #
SUPPORTED_FORMATS = {
    "DD/MM/YYYY": "%d/%m/%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
}
DEFAULT_TZ = "America/New_York"


def today_in_tz(tz_name: str) -> date:
    if ZoneInfo is None:
        return datetime.now().date()
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo(DEFAULT_TZ)
    return datetime.now(tz).date()


def _format_until_utc(d: date) -> str:
    """UNTIL must be in UTC basic format; use midnight Z of the given date."""
    return datetime.combine(d, time(0, 0), tzinfo=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_date(s: str, fmt_key: str) -> date:
    fmt = SUPPORTED_FORMATS[fmt_key]
    return datetime.strptime(s.strip(), fmt).date()


def format_date(d: date, fmt_key: str) -> str:
    fmt = SUPPORTED_FORMATS[fmt_key]
    return d.strftime(fmt)


def parse_hhmm(s: str) -> time:
    s = s.strip()
    if not s:
        raise ValueError("Enter a time like 09:30 or 17:00")
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be HH:MM")
    hh, mm = int(parts[0]), int(parts[1])
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError("Time must be 00:00 – 23:59")
    return time(hour=hh, minute=mm)


def make_ics_all_day(
    summary: str,
    d: date,
    alarms_min: list[int] | None = None,
    uid: str | None = None,
    rrule: str | None = None,
) -> str:
    """Create an all-day VEVENT with optional VALARMs and RRULE (CRLF line endings)."""
    if uid is None:
        uid = f"{uuid.uuid4()}@date-counter"
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dtstart = d.strftime("%Y%m%d")
    dtend = (d + timedelta(days=1)).strftime("%Y%m%d")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Date Counter//EN",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{summary}",
    ]
    if rrule:
        lines.append(f"RRULE:{rrule}")

    for m in (alarms_min or []):
        try:
            minutes = int(m)
        except Exception:
            continue
        lines += [
            "BEGIN:VALARM",
            f"TRIGGER:-PT{abs(minutes)}M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "END:VALARM",
        ]

    lines += [
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return _ics_join(lines)


def make_ics_timed(
    summary: str,
    start_local: datetime,
    duration_minutes: int,
    tz_name: str,
    alarms_min: list[int] | None = None,
    uid: str | None = None,
    rrule: str | None = None,
) -> str:
    """Create a timed VEVENT; export DTSTART/DTEND in UTC (…Z). Uses CRLF line endings."""
    # Normalize to UTC
    if ZoneInfo is None:
        start_dt = start_local
    else:
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo(DEFAULT_TZ)
        start_dt = start_local.replace(tzinfo=tz)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    start_utc = start_dt.astimezone(timezone.utc)
    end_utc = end_dt.astimezone(timezone.utc)
    dtstart = start_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend = end_utc.strftime("%Y%m%dT%H%M%SZ")
    tz_note = tz_name if ZoneInfo is None else start_dt.tzinfo.key  # type: ignore[attr-defined]

    if uid is None:
        uid = f"{uuid.uuid4()}@date-counter"
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Date Counter//EN",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:Time zone: {tz_note}",
    ]
    if rrule:
        lines.append(f"RRULE:{rrule}")

    for m in (alarms_min or []):
        try:
            minutes = int(m)
        except Exception:
            continue
        lines += [
            "BEGIN:VALARM",
            f"TRIGGER:-PT{abs(minutes)}M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "END:VALARM",
        ]

    lines += [
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return _ics_join(lines)

def _ics_join(lines: list[str]) -> str:
    """Join ICS lines with CRLF and end with a final CRLF."""
    return "\r\n".join(lines) + "\r\n"

# ----------------------- Google Calendar (optional) -------------------- #
@dataclass
class GoogleCalStatus:
    available: bool
    error: str | None = None


def _google_calendar_available() -> GoogleCalStatus:
    try:
        from googleapiclient.discovery import build  # noqa: F401
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401
        from google.auth.transport.requests import Request  # noqa: F401
        return GoogleCalStatus(True)
    except Exception as e:
        return GoogleCalStatus(False, str(e))


def insert_google_calendar(
    summary: str,
    all_day: bool,
    d_or_dt: date | datetime,
    duration_minutes: int | None = None,
    rrule: str | None = None,
) -> str:
    """Insert event into primary Google Calendar.
    - For all_day=True, d_or_dt is a date.
    - For all_day=False, d_or_dt is a timezone-aware datetime in local tz.
    """
    import pickle
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = pickle.loads(TOKEN_PATH.read_bytes())
        except Exception:
            creds = None
    if not creds or not getattr(creds, "valid", False):
        if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            creds.refresh(Request())
        else:
            if not CRED_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CRED_PATH}. Place your Desktop OAuth file there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_bytes(pickle.dumps(creds))

    try:
        service = build("calendar", "v3", credentials=creds)
        if all_day:
            event = {
                "summary": summary,
                "start": {"date": d_or_dt.strftime("%Y-%m-%d")},
                "end": {"date": (d_or_dt + timedelta(days=1)).strftime("%Y-%m-%d")},
            }
        else:
            start_local: datetime = d_or_dt  # type: ignore
            end_local = start_local + timedelta(minutes=duration_minutes or 60)
            event = {
                "summary": summary,
                "start": {"dateTime": start_local.isoformat()},
                "end": {"dateTime": end_local.isoformat()},
            }
        if rrule:
            event["recurrence"] = [f"RRULE:{rrule}"]

        created = service.events().insert(calendarId="primary", body=event).execute()
        html_link = created.get("htmlLink", "(no link)")
        return f"Event created: {html_link}"
    except HttpError as e:
        return f"Google Calendar API error: {e}"
    except Exception as e:
        return f"Failed to create event: {e}"

# --------------------------- Date Picker ------------------------------- #
class CalendarPopup(tk.Toplevel):
    def __init__(self, master: tk.Widget, initial: date | None = None, on_pick=None):
        super().__init__(master)
        self.title("Pick a date")
        self.resizable(False, False)
        self.on_pick = on_pick
        today = date.today() if initial is None else initial
        self.year = tk.IntVar(value=today.year)
        self.month = tk.IntVar(value=today.month)

        header = ttk.Frame(self)
        header.pack(fill="x", padx=8, pady=6)
        ttk.Button(header, text="◀", width=3, command=self.prev_month).pack(side="left")
        self.title_lbl = ttk.Label(header, text="", font=("Segoe UI", 11, "bold"))
        self.title_lbl.pack(side="left", expand=True)
        ttk.Button(header, text="▶", width=3, command=self.next_month).pack(side="right")

        grid = ttk.Frame(self)
        grid.pack(padx=8, pady=6)
        self.grid_frame = grid

        self.draw()

    def prev_month(self):
        y, m = self.year.get(), self.month.get()
        if m == 1:
            y -= 1; m = 12
        else:
            m -= 1
        self.year.set(y); self.month.set(m)
        self.draw()

    def next_month(self):
        y, m = self.year.get(), self.month.get()
        if m == 12:
            y += 1; m = 1
        else:
            m += 1
        self.year.set(y); self.month.set(m)
        self.draw()

    def draw(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        y, m = self.year.get(), self.month.get()
        self.title_lbl.config(text=f"{pycalendar.month_name[m]} {y}")
        # Weekday header
        for i, wd in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
            ttk.Label(self.grid_frame, text=wd, width=3, anchor="center").grid(row=0, column=i, padx=2, pady=2)
        # Days
        cal = pycalendar.Calendar(firstweekday=0)  # Monday
        row = 1
        for week in cal.monthdayscalendar(y, m):
            for col, d in enumerate(week):
                if d == 0:
                    ttk.Label(self.grid_frame, text="").grid(row=row, column=col, padx=1, pady=1)
                else:
                    b = ttk.Button(self.grid_frame, text=str(d), width=3,
                                   command=lambda dd=d: self.pick(date(y, m, dd)))
                    b.grid(row=row, column=col, padx=1, pady=1)
            row += 1

    def pick(self, d: date):
        if self.on_pick:
            self.on_pick(d)
        self.destroy()

# ------------------------------ GUI App ------------------------------- #
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Date Counter & .ics Maker")
        self.geometry("880x720")
        self.minsize(840, 660)
        # Modes: date_to_days, days_to_date, days_from_end
        self.mode = tk.StringVar(value="date_to_days")
        self.fmt = tk.StringVar(value="MM/DD/YYYY")
        self.tz = tk.StringVar(value=DEFAULT_TZ)
        self.custom_start_enabled = tk.BooleanVar(value=False)
        self.google_checked = tk.BooleanVar(value=False)
        self.make_ics_checked = tk.BooleanVar(value=True)
        self.timed_enabled = tk.BooleanVar(value=False)

        # Reminders
        self.reminders_var = tk.StringVar(value="60,10")
        self.duration_var = tk.StringVar(value="60")
        self.time_var = tk.StringVar(value="09:00")

        # Recurrence
        self.recur_mode = tk.StringVar(value="none")     # none, daily, weekly, monthly, yearly, custom
        self.recur_interval = tk.StringVar(value="1")    # INTERVAL
        self.recur_count = tk.StringVar(value="")        # COUNT (blank = none)
        self.recur_until = tk.StringVar(value="")        # UNTIL date in UI format
        self.recur_custom = tk.StringVar(value="")       # custom RRULE (no leading 'RRULE:')

        # Computed values
        self.computed_days: int | None = None
        self.computed_date: date | None = None
        self._build()
        self._refresh_recur()

    def _refresh_recur(self) -> None:
        mode = self.recur_mode.get()
        # Enable/disable custom field
        state_custom = "normal" if mode == "custom" else "disabled"
        self.recur_custom_entry.configure(state=state_custom)
        # Interval/Count/Until are disabled if 'none', enabled otherwise
        state_std = "disabled" if mode == "none" else "normal"
        for w in (self.recur_interval_entry,
                  self.recur_count_entry,
                  self.recur_until_entry):
            w.configure(state=state_std)
        

    def _compose_rrule(self, dt_for_freq: date | None) -> str | None:
        """Build an RRULE string from the recurrence UI. If 'none', return None."""
        mode = self.recur_mode.get()
        if mode == "none":
            return None

        if mode == "custom":
            raw = self.recur_custom.get().strip()
            if not raw:
                raise ValueError("Custom RRULE is empty.")
            # Accept with or without 'RRULE:' prefix:
            return raw[6:] if raw.upper().startswith("RRULE:") else raw

        # Preset → FREQ
        freq_map = {
            "daily": "DAILY",
            "weekly": "WEEKLY",
            "monthly": "MONTHLY",
            "yearly": "YEARLY",
        }
        if mode not in freq_map:
            return None
        parts = [f"FREQ={freq_map[mode]}"]

        # INTERVAL
        iv = self.recur_interval.get().strip()
        if iv:
            try:
                ival = int(iv)
                if ival > 1:
                    parts.append(f"INTERVAL={ival}")
            except ValueError:
                raise ValueError("Interval must be an integer.")

        # COUNT or UNTIL
        cnt = self.recur_count.get().strip()
        until_txt = self.recur_until.get().strip()
        if cnt:
            try:
                cval = int(cnt)
                if cval > 0:
                    parts.append(f"COUNT={cval}")
            except ValueError:
                raise ValueError("Count must be an integer.")
        elif until_txt:
            fmt_key = self.fmt.get()
            try:
                d_until = parse_date(until_txt, fmt_key)
            except Exception:
                raise ValueError("Invalid UNTIL date.")
            parts.append(f"UNTIL={_format_until_utc(d_until)}")
        
        return ";".join(parts)


    def _build(self) -> None:
        pad = dict(padx=10, pady=8)

        header = ttk.Label(self, text="Date Counter & .ics Maker", font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", **pad)

        # Settings
        settings = ttk.Frame(self)
        settings.pack(fill="x", **pad)
        ttk.Label(settings, text="Date format:").grid(row=0, column=0, sticky="w")
        fmt_cb = ttk.Combobox(settings, textvariable=self.fmt, values=list(SUPPORTED_FORMATS.keys()), width=14, state="readonly")
        fmt_cb.grid(row=0, column=1, sticky="w", padx=(6, 20))
        ttk.Label(settings, text="Timezone:").grid(row=0, column=2, sticky="w")
        self.tz_entry = ttk.Entry(settings, textvariable=self.tz, width=25)
        self.tz_entry.grid(row=0, column=3, sticky="w", padx=(6, 0))

        # Mode selectors
        mode_fr = ttk.LabelFrame(self, text="Mode")
        mode_fr.pack(fill="x", **pad)
        ttk.Radiobutton(mode_fr, text="1) Count days until a given end date --> (Result days between start until end) Ex. 120 days", value="date_to_days", variable=self.mode, command=self._refresh_mode).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Radiobutton(mode_fr, text="2) Add days to a start date  --> (Result end date) Ex.01/01/25", value="days_to_date", variable=self.mode, command=self._refresh_mode).grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Radiobutton(mode_fr, text="3) Subtract days from an end date --> (Result start date) Ex.19/09/25", value="days_from_end", variable=self.mode, command=self._refresh_mode).grid(row=2, column=0, sticky="w", padx=6, pady=4)

        # Inputs
        self.inputs = ttk.Frame(self)
        self.inputs.pack(fill="x", **pad)

        # End date widgets
        self.end_date_label = ttk.Label(self.inputs, text="End date:")
        self.end_date_entry = ttk.Entry(self.inputs, width=20)
        self.end_date_pick = ttk.Button(self.inputs, text="📅", width=3, command=lambda: self._open_picker(self.end_date_entry))

        # Days widgets
        self.days_label = ttk.Label(self.inputs, text="Days:")
        self.days_entry = ttk.Entry(self.inputs, width=10)

        # Custom start date
        self.custom_start_chk = ttk.Checkbutton(self.inputs, text="Use custom start date (default: today)", variable=self.custom_start_enabled, command=self._toggle_custom_start)
        self.custom_start_entry = ttk.Entry(self.inputs, width=20)
        self.custom_start_pick = ttk.Button(self.inputs, text="📅", width=3, command=lambda: self._open_picker(self.custom_start_entry))

        # Event options
        timed_fr = ttk.LabelFrame(self, text="Event options (.ics / Google)")
        timed_fr.pack(fill="x", **pad)
        self.timed_chk = ttk.Checkbutton(timed_fr, text="Timed event (otherwise all-day)", variable=self.timed_enabled, command=self._refresh_timed)
        self.timed_chk.grid(row=0, column=0, sticky="w")
        ttk.Label(timed_fr, text="Start time HH:MM:").grid(row=1, column=0, sticky="w", padx=(0,6))
        self.time_entry = ttk.Entry(timed_fr, textvariable=self.time_var, width=8)
        self.time_entry.grid(row=1, column=1, sticky="w")
        ttk.Label(timed_fr, text="Duration (min):").grid(row=1, column=2, sticky="w", padx=(16,6))
        self.duration_entry = ttk.Entry(timed_fr, textvariable=self.duration_var, width=8)
        self.duration_entry.grid(row=1, column=3, sticky="w")
        ttk.Label(timed_fr, text="Reminders (min before, comma):").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.reminders_entry = ttk.Entry(timed_fr, textvariable=self.reminders_var, width=20)
        self.reminders_entry.grid(row=2, column=1, sticky="w", pady=(6,0))

        # Recurrence (optional)
        recur_fr = ttk.LabelFrame(self, text="Recurrence (optional)")
        recur_fr.pack(fill="x", padx=10, pady=6)

        ttk.Label(recur_fr, text="Pattern:").grid(row=0, column=0, sticky="w")
        self.recur_mode_cb = ttk.Combobox(
            recur_fr, width=16, state="readonly", textvariable=self.recur_mode,
            values=["none", "daily", "weekly", "monthly", "yearly", "custom"]
        )
        self.recur_mode_cb.grid(row=0, column=1, sticky="w", padx=(6, 16))
        self.recur_mode_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_recur())

        ttk.Label(recur_fr, text="Interval:").grid(row=0, column=2, sticky="w")
        self.recur_interval_entry = ttk.Entry(recur_fr, width=6, textvariable=self.recur_interval)
        self.recur_interval_entry.grid(row=0, column=3, sticky="w", padx=(6, 16))

        ttk.Label(recur_fr, text="Count:").grid(row=0, column=4, sticky="w")
        self.recur_count_entry = ttk.Entry(recur_fr, width=6, textvariable=self.recur_count)
        self.recur_count_entry.grid(row=0, column=5, sticky="w", padx=(6, 16))

        ttk.Label(recur_fr, text="Until:").grid(row=0, column=6, sticky="w")
        self.recur_until_entry = ttk.Entry(recur_fr, width=12, textvariable=self.recur_until)
        self.recur_until_entry.grid(row=0, column=7, sticky="w", padx=(6, 4))
        ttk.Button(recur_fr, text="📅", width=3,
                   command=lambda: self._open_picker(self.recur_until_entry)).grid(row=0, column=8, sticky="w")

        ttk.Label(recur_fr, text="Custom RRULE:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.recur_custom_entry = ttk.Entry(recur_fr, width=64, textvariable=self.recur_custom)
        self.recur_custom_entry.grid(row=1, column=1, columnspan=7, sticky="w", padx=(6,0), pady=(6,0))

        # Title
        ttk.Label(self.inputs, text="Event title:").grid(row=99, column=0, sticky="w")
        self.title_entry = ttk.Entry(self.inputs, width=40)
        self.title_entry.insert(0, "Happy New Year")
        self.title_entry.grid(row=99, column=1, sticky="w", padx=(8, 0))

        # Options
        opts = ttk.Frame(self)
        opts.pack(fill="x", **pad)
        self.ics_chk = ttk.Checkbutton(opts, text="Create .ics after compute", variable=self.make_ics_checked)
        self.ics_chk.grid(row=0, column=0, sticky="w")
        gstat = _google_calendar_available()
        gtext = "Also insert into Google Calendar" if gstat.available else "(Google Calendar libs not found — install to enable)"
        self.google_chk = ttk.Checkbutton(opts, text=gtext, variable=self.google_checked, state=("!disabled" if gstat.available else "disabled"))
        self.google_chk.grid(row=0, column=1, sticky="w", padx=(20, 0))

        # Actions
        actions = ttk.Frame(self)
        actions.pack(fill="x", **pad)
        self.compute_btn = ttk.Button(actions, text="Compute", command=self._compute)
        self.compute_btn.grid(row=0, column=0, padx=(0, 10))
        self.save_btn = ttk.Button(actions, text="Save .ics…", command=self._save_ics, state="disabled")
        self.save_btn.grid(row=0, column=1, padx=(0, 10))
        self.quit_btn = ttk.Button(actions, text="Quit", command=self.destroy)
        self.quit_btn.grid(row=0, column=2)

        # Output
        out_fr = ttk.LabelFrame(self, text="Result")
        out_fr.pack(fill="both", expand=True, **pad)
        self.output = tk.Text(out_fr, height=10, wrap="word")
        self.output.pack(fill="both", expand=True, padx=8, pady=8)

        self._refresh_mode()
        self._refresh_timed()

    def _compose_rrule(self, dt_for_freq: date | None) -> str | None:
        """Build an RRULE string from the recurrence UI. If 'none', return None."""
        mode = self.recur_mode.get()
        if mode == "none":
            return None

        if mode == "custom":
            raw = self.recur_custom.get().strip()
            if not raw:
                raise ValueError("Custom RRULE is empty.")
            # Accept with or without 'RRULE:' prefix:
            return raw[6:] if raw.upper().startswith("RRULE:") else raw

        # Preset → FREQ
        freq_map = {
            "daily": "DAILY",
            "weekly": "WEEKLY",
            "monthly": "MONTHLY",
            "yearly": "YEARLY",
        }
        if mode not in freq_map:
            return None
        parts = [f"FREQ={freq_map[mode]}"]

        # INTERVAL
        iv = self.recur_interval.get().strip()
        if iv:
            try:
                ival = int(iv)
                if ival > 1:
                    parts.append(f"INTERVAL={ival}")
            except ValueError:
                raise ValueError("Interval must be an integer.")

        # COUNT or UNTIL
        cnt = self.recur_count.get().strip()
        until_txt = self.recur_until.get().strip()
        if cnt:
            try:
                cval = int(cnt)
                if cval > 0:
                    parts.append(f"COUNT={cval}")
            except ValueError:
                raise ValueError("Count must be an integer.")
        elif until_txt:
            fmt_key = self.fmt.get()
            try:
                d_until = parse_date(until_txt, fmt_key)
            except Exception:
                raise ValueError("Invalid UNTIL date.")
            parts.append(f"UNTIL={_format_until_utc(d_until)}")

        return ";".join(parts)

    def _open_picker(self, target_entry: ttk.Entry):
        try:
            d = parse_date(target_entry.get().strip(), self.fmt.get())
        except Exception:
            d = date.today()
        def on_pick(dpicked: date):
            target_entry.delete(0, tk.END)
            target_entry.insert(0, format_date(dpicked, self.fmt.get()))
        CalendarPopup(self, initial=d, on_pick=on_pick)

    def _place_input_rows(self) -> None:
        for child in self.inputs.grid_slaves():
            child.grid_forget()
        row = 0
        m = self.mode.get()
        if m == "date_to_days":
            self.end_date_label.grid(row=row, column=0, sticky="w")
            self.end_date_entry.grid(row=row, column=1, sticky="w", padx=(8, 0))
            self.end_date_pick.grid(row=row, column=2, sticky="w", padx=(6,0))
            row += 1
        elif m == "days_to_date":
            self.days_label.configure(text="Days from start:")
            self.days_label.grid(row=row, column=0, sticky="w")
            self.days_entry.grid(row=row, column=1, sticky="w", padx=(8, 0))
            row += 1
        else:  # days_from_end
            self.end_date_label.grid(row=row, column=0, sticky="w")
            self.end_date_entry.grid(row=row, column=1, sticky="w", padx=(8, 0))
            self.end_date_pick.grid(row=row, column=2, sticky="w", padx=(6,0))
            row += 1
            self.days_label.configure(text="Days to subtract:")
            self.days_label.grid(row=row, column=0, sticky="w")
            self.days_entry.grid(row=row, column=1, sticky="w", padx=(8, 0))
            row += 1

        if m in ("date_to_days", "days_to_date"):
            self.custom_start_chk.grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 2))
            row += 1
            if self.custom_start_enabled.get():
                ttk.Label(self.inputs, text="Custom start date:").grid(row=row, column=0, sticky="w")
                self.custom_start_entry.grid(row=row, column=1, sticky="w", padx=(8, 0))
                self.custom_start_pick.grid(row=row, column=2, sticky="w", padx=(6,0))
                row += 1
        else:
            self.custom_start_enabled.set(False)

        ttk.Label(self.inputs, text="Event title:").grid(row=row, column=0, sticky="w")
        self.title_entry.grid(row=row, column=1, sticky="w", padx=(8, 0))

    def _refresh_mode(self) -> None:
        self._place_input_rows()
        self._toggle_custom_start()
        self._set_output("")
        self.save_btn.configure(state="disabled")

    def _refresh_timed(self) -> None:
        state = "!disabled" if self.timed_enabled.get() else "disabled"
        for w in (self.time_entry, self.duration_entry):
            w.configure(state=state)

    def _toggle_custom_start(self) -> None:
        if self.custom_start_enabled.get():
            self.custom_start_entry.configure(state="normal")
            self.custom_start_entry.delete(0, tk.END)
            self.custom_start_entry.insert(0, self._today_str())
        else:
            self.custom_start_entry.configure(state="disabled")

    def _today_str(self) -> str:
        return format_date(today_in_tz(self.tz.get().strip() or DEFAULT_TZ), self.fmt.get())

    def _set_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    # --------------------------- Core Logic ---------------------------- #
    def _compute(self) -> None:
        try:
            fmt_key = self.fmt.get()
            tz_name = self.tz.get().strip() or DEFAULT_TZ
            mode = self.mode.get()

            if mode in ("date_to_days", "days_to_date"):
                if self.custom_start_enabled.get():
                    s = self.custom_start_entry.get().strip()
                    if not s:
                        raise ValueError("Please enter a custom start date or uncheck the option.")
                    start = parse_date(s, fmt_key)
                else:
                    start = today_in_tz(tz_name)
            else:
                start = None

            if mode == "date_to_days":
                end_str = self.end_date_entry.get().strip()
                if not end_str:
                    raise ValueError("Please enter an end date.")
                end = parse_date(end_str, fmt_key)
                delta_days = (end - start).days  # type: ignore[arg-type]
                self.computed_days = delta_days
                self.computed_date = end
                abs_days = abs(delta_days)
                dir_word = "ahead" if delta_days >= 0 else "ago"
                txt = (
                    f"Start: {format_date(start, fmt_key)}"  # type: ignore[arg-type]
                    f"End:   {format_date(end, fmt_key)}"
                    f"Result: {delta_days} day(s) ({abs_days} {dir_word} of start)."
                )

            elif mode == "days_to_date":
                days_str = self.days_entry.get().strip()
                if not days_str:
                    raise ValueError("Please enter a number of days.")
                try:
                    n = int(days_str)
                except ValueError:
                    raise ValueError("Days must be an integer (e.g., 121 or -7).")
                end = start + timedelta(days=n)  # type: ignore[operator]
                self.computed_days = n
                self.computed_date = end
                direction = "from" if n >= 0 else "before"
                txt = (
                    f"Start: {format_date(start, fmt_key)}"  # type: ignore[arg-type]
                    f"Days:  {n}"
                    f"Result: {format_date(end, fmt_key)} ({abs(n)} day(s) {direction} start)."
                )

            else:  # days_from_end
                end_str = self.end_date_entry.get().strip()
                if not end_str:
                    raise ValueError("Please enter an end date.")
                days_str = self.days_entry.get().strip()
                if not days_str:
                    raise ValueError("Please enter days to subtract.")
                try:
                    n = int(days_str)
                except ValueError:
                    raise ValueError("Days must be an integer (e.g., 121).")
                end = parse_date(end_str, fmt_key)
                start_calc = end - timedelta(days=n)
                self.computed_days = n
                self.computed_date = start_calc
                txt = (
                    f"End:   {format_date(end, fmt_key)}"
                    f"Days to subtract: {n}"
                    f"Result (start date): {format_date(start_calc, fmt_key)}."
                )

            # Build RRULE from UI (None if off)
            rrule = self._compose_rrule(self.computed_date)

            # Build ICS + Google actions (use computed_date)
            did_any = False
            status_lines = []

            alarms: list[int] = []
            rem_raw = self.reminders_var.get().strip()
            if rem_raw:
                for token in rem_raw.split(',')[:3]:
                    try:
                        alarms.append(int(token.strip()))
                    except Exception:
                        pass

            title = self.title_entry.get().strip() or "Reminder"

            if self.timed_enabled.get():
                if self.computed_date is None:
                    raise ValueError("No target date computed yet.")
                hhmm = parse_hhmm(self.time_var.get())
                if ZoneInfo is not None:
                    try:
                        tz = ZoneInfo(tz_name)
                    except Exception:
                        tz = ZoneInfo(DEFAULT_TZ)
                    start_dt_local = datetime.combine(self.computed_date, hhmm).replace(tzinfo=tz)
                else:
                    start_dt_local = datetime.combine(self.computed_date, hhmm)
                duration_min = int(self.duration_var.get().strip() or 60)

                if self.make_ics_checked.get():
                    ics_str = make_ics_timed(title, start_dt_local, duration_min, tz_name, alarms, rrule=rrule)
                    self._cached_ics = ics_str
                    self.save_btn.configure(state="normal")
                    status_lines.append(".ics (timed) ready — click 'Save .ics…'.")
                    did_any = True

                if self.google_checked.get():
                    try:
                        res = insert_google_calendar(title, False, start_dt_local, duration_min, rrule=rrule)
                        status_lines.append(res)
                        did_any = True
                    except Exception as e:
                        status_lines.append(f"Google Calendar insert failed: {e}")
            else:
                if self.computed_date is None:
                    raise ValueError("No target date computed yet.")
                if self.make_ics_checked.get():
                    ics_str = make_ics_all_day(title, self.computed_date, alarms, rrule=rrule)
                    self._cached_ics = ics_str
                    self.save_btn.configure(state="normal")
                    status_lines.append(".ics (all-day) ready — click 'Save .ics…'.")
                    did_any = True
                if self.google_checked.get():
                    try:
                        res = insert_google_calendar(title, True, self.computed_date, rrule=rrule)
                        status_lines.append(res)
                        did_any = True
                    except Exception as e:
                        status_lines.append(f"Google Calendar insert failed: {e}")

            if not did_any:
                status_lines.append("(No .ics or Google insert selected.)")

            self._set_output(txt + "" + "".join(status_lines))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_ics(self) -> None:
        ics_data = getattr(self, "_cached_ics", None)
        if not ics_data:
            messagebox.showwarning("Nothing to save", "Compute first to generate an .ics event.")
            return
        default_name = "reminder.ics"
        path = filedialog.asksaveasfilename(
            title="Save .ics",
            defaultextension=".ics",
            initialfile=default_name,
            filetypes=[("iCalendar file", ".ics"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(ics_data)
            messagebox.showinfo("Saved", f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))


if __name__ == "__main__":
    app = App()
    app.mainloop()
