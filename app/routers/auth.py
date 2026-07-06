from app.templating import templates
import secrets
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.deps import base_context, check_csrf, flash, set_old, get_csrf_token
from app.models.user import User

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", base_context(request))


@router.get("/register", response_class=HTMLResponse)
def show_register(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("auth/register.html", base_context(request))


@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    remember: str = Form(default=None),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)

    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password):
        set_old(request, {"email": email})
        ctx = base_context(request, errors={"email": "Credenciales incorrectas."})
        return templates.TemplateResponse("auth/login.html", ctx, status_code=422)

    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=302)


@router.post("/register")
async def register(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirmation: str = Form(...),
    company: str = Form(default=""),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    errors = {}

    if len(name) > 100:
        errors["name"] = "El nombre no puede superar 100 caracteres."
    if password != password_confirmation:
        errors["password"] = "Las contraseñas no coinciden."
    if len(password) < 8:
        errors["password"] = "La contraseña debe tener al menos 8 caracteres."
    if db.query(User).filter(User.email == email).first():
        errors["email"] = "Este email ya está registrado."

    if errors:
        set_old(request, {"name": name, "email": email, "company": company})
        ctx = base_context(request, errors=errors)
        return templates.TemplateResponse("auth/register.html", ctx, status_code=422)

    user = User(
        name=name,
        email=email,
        password=pwd_context.hash(password),
        api_key="mb_live_" + secrets.token_hex(16),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    flash(request, f"api_key:{user.api_key}", "api_key_new")
    return RedirectResponse("/dashboard", status_code=302)


@router.post("/logout")
async def logout(request: Request, csrf_token: str = Form(...)):
    check_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

