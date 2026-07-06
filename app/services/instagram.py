import httpx

API_BASE = "https://graph.facebook.com/v19.0"


def send_text(account, recipient_id: str, text: str) -> dict:
    url = f"{API_BASE}/{account.platform_account_id}/messages"
    r = httpx.post(
        url,
        json={"recipient": {"id": recipient_id}, "message": {"text": text}},
        headers={"Authorization": f"Bearer {account.access_token}"},
        timeout=15,
    )
    return r.json()


def reply_to_story(account, recipient_id: str, text: str) -> dict:
    return send_text(account, recipient_id, text)
