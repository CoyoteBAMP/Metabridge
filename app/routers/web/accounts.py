from app.templating import templates
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.deps import require_auth, base_context, check_csrf, flash, set_old

from app.models.connected_account import ConnectedAccount

router = APIRouter()


@router.get("/accounts", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    accounts = db.query(ConnectedAccount).filter(ConnectedAccount.user_id == current_user.id).all()
    ctx = base_context(request, current_user)
    ctx["accounts"] = accounts
    return templates.TemplateResponse("accounts/index.html", ctx)


@router.post("/accounts")
async def store(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    platform: str = Form(...),
    name: str = Form(...),
    platform_account_id: str = Form(...),
    access_token: str = Form(...),
    phone_number_id: str = Form(default=""),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)

    try:
        existing = db.query(ConnectedAccount).filter(
            ConnectedAccount.platform_account_id == platform_account_id,
            ConnectedAccount.platform == platform,
        ).first()

        if existing:
            existing.user_id = current_user.id
            existing.name = name
            existing.access_token = access_token
            existing.phone_number_id = phone_number_id or None
            existing.active = True
        else:
            account = ConnectedAccount(
                user_id=current_user.id,
                platform=platform,
                platform_account_id=platform_account_id,
                name=name,
                access_token=access_token,
                phone_number_id=phone_number_id or None,
                active=True,
            )
            db.add(account)

        db.commit()
    except IntegrityError:
        db.rollback()
        set_old(request, {"platform": platform, "name": name, "platform_account_id": platform_account_id})
        ctx = base_context(request, current_user, errors={"platform_account_id": "Esta cuenta ya está registrada por otro usuario."})
        ctx["accounts"] = db.query(ConnectedAccount).filter(ConnectedAccount.user_id == current_user.id).all()
        return templates.TemplateResponse("accounts/index.html", ctx, status_code=422)

    flash(request, "Cuenta conectada correctamente.")
    return RedirectResponse("/accounts", status_code=302)


@router.post("/accounts/{account_id}/toggle")
async def toggle(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id, ConnectedAccount.user_id == current_user.id
    ).first()
    if account:
        account.active = not account.active
        db.commit()
        flash(request, "Estado actualizado.")
    return RedirectResponse("/accounts", status_code=302)


@router.post("/accounts/{account_id}/delete")
async def destroy(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id, ConnectedAccount.user_id == current_user.id
    ).first()
    if account:
        db.delete(account)
        db.commit()
        flash(request, "Cuenta eliminada.")
    return RedirectResponse("/accounts", status_code=302)

