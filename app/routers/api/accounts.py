from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.deps import get_api_user
from app.models.connected_account import ConnectedAccount

router = APIRouter()


class AccountCreate(BaseModel):
    platform: str
    platform_account_id: str
    name: Optional[str] = None
    access_token: str
    phone_number_id: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    access_token: Optional[str] = None
    active: Optional[bool] = None


def _account_or_404(account_id: int, user_id: int, db: Session) -> ConnectedAccount:
    a = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id, ConnectedAccount.user_id == user_id
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    return a


@router.get("/accounts")
def index(db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    accounts = db.query(ConnectedAccount).filter(ConnectedAccount.user_id == current_user.id).all()
    return [{"id": a.id, "platform": a.platform, "name": a.name, "active": a.active} for a in accounts]


@router.post("/accounts", status_code=201)
def store(body: AccountCreate, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    if body.platform not in ("whatsapp", "facebook", "instagram"):
        raise HTTPException(status_code=422, detail="Plataforma inválida.")
    account = ConnectedAccount(user_id=current_user.id, **body.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"id": account.id, "platform": account.platform, "name": account.name, "active": account.active}


@router.get("/accounts/{account_id}")
def show(account_id: int, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    a = _account_or_404(account_id, current_user.id, db)
    return {"id": a.id, "platform": a.platform, "name": a.name, "active": a.active}


@router.put("/accounts/{account_id}")
def update(account_id: int, body: AccountUpdate, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    a = _account_or_404(account_id, current_user.id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(a, field, value)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "platform": a.platform, "name": a.name, "active": a.active}


@router.delete("/accounts/{account_id}", status_code=204)
def destroy(account_id: int, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    a = _account_or_404(account_id, current_user.id, db)
    db.delete(a)
    db.commit()
