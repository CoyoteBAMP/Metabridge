import itertools
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Optional

_lock = threading.Lock()
_events = deque(maxlen=200)
_counter = itertools.count(1)


def record_event(
    kind: str,
    status: str,
    platform: Optional[str] = None,
    detail: Optional[str] = None,
    payload: Optional[dict] = None,
) -> dict:
    """Guarda un evento en el buffer en memoria para poder verlo en /monitor.

    kind: "verify" (GET de validación) | "event" (POST con datos)
    status: "ok" | "ignored" | "account_not_found" | "forbidden" | "invalid_json" | "error"
    """
    event = {
        "id": next(_counter),
        "at": datetime.now(timezone.utc),
        "kind": kind,
        "status": status,
        "platform": platform,
        "detail": detail,
        "payload": payload,
    }
    with _lock:
        _events.appendleft(event)
    return event


def get_events(limit: int = 100) -> list:
    with _lock:
        return list(_events)[:limit]


def clear_events() -> None:
    with _lock:
        _events.clear()
