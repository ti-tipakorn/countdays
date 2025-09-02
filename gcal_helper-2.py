from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_calendar_service():
    # --- Diagnostics ---
    print(f"[auth] Script folder: {APP_DIR}")
    print(f"[auth] Looking for credentials at: {CRED_PATH}")
    print(f"[auth] Exists? {CRED_PATH.exists()}")

    creds = None
    if TOKEN_PATH.exists():
        try:
            with TOKEN_PATH.open("rb") as f:
                creds = pickle.load(f)
        except Exception as e:
            print(f"[auth] token.pickle unreadable, will re-auth: {e}")

    if not creds or not getattr(creds, "valid", False):
        if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            print("[auth] Refreshing expired token…")
            creds.refresh(Request())
        else:
            if not CRED_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CRED_PATH}. "
                    "Make sure it's the OAuth *Desktop app* client."
                )
            print("[auth] Launching OAuth browser flow…")
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with TOKEN_PATH.open("wb") as f:
            pickle.dump(creds, f)
            print(f"[auth] Saved token to {TOKEN_PATH}")

    print("[auth] Calendar service ready.")
    return build("calendar", "v3", credentials=creds)
