from app.templating import templates
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth, base_context, check_csrf, flash
from app.models.message_template import MessageTemplate

router = APIRouter()

CATEGORIES = ["general", "saludo", "pedido", "soporte"]


@router.get("/templates", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    tpls = db.query(MessageTemplate).filter(
        MessageTemplate.user_id == current_user.id
    ).order_by(MessageTemplate.category, MessageTemplate.name).all()

    ctx = base_context(request, current_user)
    ctx["templates"] = tpls
    return templates.TemplateResponse("templates_tpl/index.html", ctx)


@router.post("/templates")
async def store(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    name: str = Form(...),
    body: str = Form(...),
    category: str = Form(...),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)

    if category not in CATEGORIES:
        ctx = base_context(request, current_user, errors={"category": "Categoría inválida."})
        ctx["templates"] = db.query(MessageTemplate).filter(MessageTemplate.user_id == current_user.id).all()
        return templates.TemplateResponse("templates_tpl/index.html", ctx, status_code=422)

    tpl = MessageTemplate(user_id=current_user.id, name=name, body=body, category=category)
    db.add(tpl)
    db.commit()
    flash(request, "Plantilla creada.")
    return RedirectResponse("/templates", status_code=302)


@router.post("/templates/{tpl_id}/update")
async def update(
    tpl_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    name: str = Form(...),
    body: str = Form(...),
    category: str = Form(...),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    tpl = db.query(MessageTemplate).filter(
        MessageTemplate.id == tpl_id, MessageTemplate.user_id == current_user.id
    ).first()
    if tpl:
        tpl.name = name
        tpl.body = body
        tpl.category = category
        db.commit()
        flash(request, "Plantilla actualizada.")
    return RedirectResponse("/templates", status_code=302)


@router.post("/templates/{tpl_id}/delete")
async def destroy(
    tpl_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    tpl = db.query(MessageTemplate).filter(
        MessageTemplate.id == tpl_id, MessageTemplate.user_id == current_user.id
    ).first()
    if tpl:
        db.delete(tpl)
        db.commit()
        flash(request, "Plantilla eliminada.")
    return RedirectResponse("/templates", status_code=302)

