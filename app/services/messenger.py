import httpx

API_URL = "https://graph.facebook.com/v19.0/me/messages"


def send_text(account, recipient_id: str, text: str) -> dict:
    r = httpx.post(
        API_URL,
        json={"recipient": {"id": recipient_id}, "message": {"text": text}},
        headers={"Authorization": f"Bearer {account.access_token}"},
        timeout=15,
    )
    return r.json()


def send_quick_replies(account, recipient_id: str, text: str, options: list) -> dict:
    quick_replies = [
        {"content_type": "text", "title": o["title"], "payload": o["payload"]}
        for o in options
    ]
    r = httpx.post(
        API_URL,
        json={
            "recipient": {"id": recipient_id},
            "message": {"text": text, "quick_replies": quick_replies},
        },
        headers={"Authorization": f"Bearer {account.access_token}"},
        timeout=15,
    )
    return r.json()
