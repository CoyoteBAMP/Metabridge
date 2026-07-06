import secrets
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db


def get_csrf_token(request: Request) -> str:
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_hex(32)
    return request.session["csrf_token"]


def flash(request: Request, message: str, category: str = "success"):
    if "flash" not in request.session:
        request.session["flash"] = []
    flashes = list(request.session.get("flash", []))
    flashes.append({"message": message, "category": category})
    request.session["flash"] = flashes


def get_flashes(request: Request) -> list:
    flashes = list(request.session.get("flash", []))
    request.session["flash"] = []
    return flashes


def set_old(request: Request, data: dict):
    request.session["old"] = data


def get_old(request: Request) -> dict:
    old = dict(request.session.get("old", {}))
    request.session["old"] = {}
    return old


def base_context(request: Request, current_user=None, errors: dict | list = None) -> dict:
    return {
        "request": request,
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
        "flashes": get_flashes(request),
        "errors": errors or {},
        "old": get_old(request),
        "app_url": request.base_url,
    }


def check_csrf(request: Request, form_token: Optional[str]):
    session_token = request.session.get("csrf_token")
    if not session_token or session_token != form_token:
        raise HTTPException(status_code=403, detail="CSRF token inválido")


async def get_current_user_web(request: Request, db: Session = Depends(get_db)):
    from app.models.user import User
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


async def require_auth(request: Request, db: Session = Depends(get_db)):
    from app.models.user import User
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user


async def get_api_user(request: Request, db: Session = Depends(get_db)):
    from app.models.user import User
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key requerida")
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="API key inválida")
    return user
