import os
import requests as _requests
from datetime import timezone, timedelta
from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

JST = timezone(timedelta(hours=9))
LABEL_NAME = "⚑要返信"
_creds_cache: Credentials | None = None


def _get_creds() -> Credentials:
    global _creds_cache
    if _creds_cache and _creds_cache.valid:
        return _creds_cache
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
    creds.refresh(Request())
    _creds_cache = creds
    return creds


def _api(path: str, **kwargs) -> dict:
    creds = _get_creds()
    resp = _requests.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/{path}",
        headers={"Authorization": f"Bearer {creds.token}"},
        **kwargs,
    )
    resp.raise_for_status()
    return resp.json()


def get_unreplied() -> list[dict]:
    """⚑要返信ラベル付きスレッドを収集する（ラベリングはclaude.aiルーティンに委譲）"""
    data = _api("threads", params={
        "q": f"label:{LABEL_NAME}",
        "maxResults": 50,
    })

    results = []
    for thread in data.get("threads", []):
        try:
            t = _api(f"threads/{thread['id']}", params={
                "format": "metadata",
                "metadataHeaders": ["Subject", "From", "Date"],
            })
            messages = t.get("messages", [])
            if not messages:
                continue
            headers = {h["name"]: h["value"] for h in messages[-1].get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "（件名なし）")
            sender = headers.get("From", "不明")
            if "<" in sender:
                sender = sender[:sender.index("<")].strip().strip('"')
            date_str = headers.get("Date", "")
            try:
                time_str = parsedate_to_datetime(date_str).astimezone(JST).strftime("%m/%d %H:%M")
            except Exception:
                time_str = ""
            results.append({
                "subject": subject[:50],
                "sender": sender,
                "time": time_str,
                "url": f"https://mail.google.com/mail/u/0/#inbox/{thread['id']}",
            })
        except Exception:
            continue
    return results
