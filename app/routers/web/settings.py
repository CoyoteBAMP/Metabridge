from app.templating import templates
import secrets
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth, base_context, check_csrf, flash

router = APIRouter()


@router.get("/settings/api-key", response_class=HTMLResponse)
async def api_key(request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    ctx = base_context(request, current_user)
    return templates.TemplateResponse("settings/apikey.html", ctx)


@router.post("/settings/api-key/regenerate")
async def regenerate_key(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    new_key = "mb_live_" + secrets.token_hex(16)
    current_user.api_key = new_key
    db.commit()
    flash(request, f"api_key:{new_key}", "api_key_new")
    return RedirectResponse("/settings/api-key", status_code=302)

