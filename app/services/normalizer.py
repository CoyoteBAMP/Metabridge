from typing import Optional


def detect_platform(payload: dict) -> Optional[str]:
    if (payload.get("object")) == "instagram":
        return "instagram"
    try:
        if payload["entry"][0]["changes"][0]["value"]["messaging_product"]:
            return "whatsapp"
    except (KeyError, IndexError):
        pass
    try:
        if payload["entry"][0]["messaging"]:
            return "facebook"
    except (KeyError, IndexError):
        pass
    return None


def normalize(platform: str, payload: dict) -> Optional[dict]:
    if platform == "whatsapp":
        return _normalize_whatsapp(payload)
    if platform == "facebook":
        return _normalize_facebook(payload)
    if platform == "instagram":
        return _normalize_instagram(payload)
    return None


def _normalize_whatsapp(payload: dict) -> Optional[dict]:
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
    except (KeyError, IndexError):
        return None

    return {
        "platform": "whatsapp",
        "from": message["from"],
        "platform_msg_id": message["id"],
        "type": message.get("type", "other"),
        "content": _extract_whatsapp_content(message),
        "timestamp": message["timestamp"],
        "contact_name": value.get("contacts", [{}])[0].get("profile", {}).get("name"),
        "account_id": value.get("metadata", {}).get("phone_number_id"),
    }


def _normalize_facebook(payload: dict) -> Optional[dict]:
    try:
        messaging = payload["entry"][0]["messaging"][0]
    except (KeyError, IndexError):
        return None

    if not messaging.get("message"):
        return None
    if messaging["message"].get("is_echo"):
        return None

    return {
        "platform": "facebook",
        "from": messaging["sender"]["id"],
        "platform_msg_id": messaging["message"]["mid"],
        "type": "image" if messaging["message"].get("attachments") else "text",
        "content": {"text": messaging["message"].get("text")},
        "timestamp": str(messaging["timestamp"]),
        "contact_name": None,
        "account_id": payload["entry"][0]["id"],
    }


def _normalize_instagram(payload: dict) -> Optional[dict]:
    try:
        messaging = payload["entry"][0]["messaging"][0]
    except (KeyError, IndexError):
        return None

    if not messaging.get("message"):
        return None
    if messaging["message"].get("is_echo"):
        return None

    return {
        "platform": "instagram",
        "from": messaging["sender"]["id"],
        "platform_msg_id": messaging["message"]["mid"],
        "type": "text",
        "content": {"text": messaging["message"].get("text")},
        "timestamp": str(messaging["timestamp"]),
        "contact_name": None,
        "account_id": payload["entry"][0]["id"],
    }


def _extract_whatsapp_content(message: dict) -> dict:
    t = message.get("type", "other")
    if t == "text":
        return {"text": message.get("text", {}).get("body")}
    if t == "image":
        return {"url": message.get("image", {}).get("url"), "caption": message.get("image", {}).get("caption")}
    if t == "audio":
        return {"url": message.get("audio", {}).get("url")}
    if t == "video":
        return {"url": message.get("video", {}).get("url")}
    if t == "document":
        return {"url": message.get("document", {}).get("url"), "filename": message.get("document", {}).get("filename")}
    return message.get(t, {})
