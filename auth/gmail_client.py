import base64
import json
from email.mime.text import MIMEText
import requests
from auth.gmail_oauth import get_access_token, refresh_token, is_logged_in

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def _get_headers():
    token = get_access_token()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def _request(method, url, **kwargs):
    headers = _get_headers()
    if not headers:
        return None, "Not logged in. Run: /gmail login"

    response = requests.request(method, url, headers=headers, **kwargs)

    if response.status_code == 401:
        new_token = refresh_token()
        if new_token:
            headers = {"Authorization": f"Bearer {new_token['access_token']}"}
            response = requests.request(method, url, headers=headers, **kwargs)

    if response.status_code >= 400:
        return None, f"API Error: {response.text}"

    return response.json(), None


def get_profile():
    data, err = _request("GET", f"{GMAIL_API_BASE}/profile")
    if err:
        return None, err
    return {"email": data["emailAddress"], "messages_total": data["messagesTotal"]}, None


def list_messages(query="is:unread", max_results=10):
    params = {"q": query, "maxResults": max_results}
    data, err = _request("GET", f"{GMAIL_API_BASE}/messages", params=params)
    if err:
        return [], err
    messages = data.get("messages", [])
    return messages, None


def get_message(msg_id):
    data, err = _request("GET", f"{GMAIL_API_BASE}/messages/{msg_id}", params={"format": "full"})
    if err:
        return None, err

    headers = {h["name"].lower(): h["value"] for h in data.get("payload", {}).get("headers", [])}
    body = _extract_body(data.get("payload", {}))

    return {
        "id": msg_id,
        "thread_id": data.get("threadId"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "body": body,
        "snippet": data.get("snippet", "")
    }, None


def _extract_body(payload):
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            nested = _extract_body(part)
            if nested:
                return nested
    return ""


def send_message(to, subject, body):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    payload = {"raw": raw}

    data, err = _request("POST", f"{GMAIL_API_BASE}/messages/send", json=payload)
    if err:
        return None, err
    return {"id": data["id"]}, None


def mark_read(msg_id):
    payload = {"removeLabelIds": ["UNREAD"]}
    data, err = _request("POST", f"{GMAIL_API_BASE}/messages/{msg_id}/modify", json=payload)
    return err is None, err


def get_unread(max_results=10):
    messages, err = list_messages("is:unread", max_results)
    if err:
        return [], err

    emails = []
    for msg in messages:
        email, err = get_message(msg["id"])
        if not err:
            emails.append(email)

    return emails, None
