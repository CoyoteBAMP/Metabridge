from app.templating import templates
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.deps import require_auth, base_context
from app.webhook_monitor import get_events

router = APIRouter()


@router.get("/monitor", response_class=HTMLResponse)
async def index(request: Request, current_user=Depends(require_auth)):
    ctx = base_context(request, current_user)
    ctx["events"] = get_events()
    return templates.TemplateResponse("monitor/index.html", ctx)
