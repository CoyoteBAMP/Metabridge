from datetime import datetime, timezone
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def _humanize_time(dt) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - dt
    s = int(diff.total_seconds())
    if s < 60:
        return "hace unos segundos"
    if s < 3600:
        m = s // 60
        return f"hace {m} {'minuto' if m == 1 else 'minutos'}"
    if s < 86400:
        h = s // 3600
        return f"hace {h} {'hora' if h == 1 else 'horas'}"
    if s < 604800:
        d = s // 86400
        return f"hace {d} {'día' if d == 1 else 'días'}"
    return dt.strftime("%d/%m/%Y")


def _format_number(n) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


templates.env.filters["humanize"] = _humanize_time
templates.env.filters["format_number"] = _format_number
