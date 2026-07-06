import httpx

API_URL = "https://graph.facebook.com/v19.0"


def send_message(account, to: str, payload: dict) -> dict:
    data = {"messaging_product": "whatsapp", "to": to, **payload}
    r = httpx.post(
        f"{API_URL}/{account.phone_number_id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {account.access_token}"},
        timeout=15,
    )
    return r.json()


def send_text(account, to: str, text: str) -> dict:
    return send_message(account, to, {"type": "text", "text": {"body": text}})


def send_template(account, to: str, template_name: str, lang: str = "es") -> dict:
    return send_message(account, to, {
        "type": "template",
        "template": {"name": template_name, "language": {"code": lang}},
    })
