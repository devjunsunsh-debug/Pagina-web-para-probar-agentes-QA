"""Login y logout (PBI 9)."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import (
    esta_bloqueado,
    login_user,
    logout_user,
    registrar_intento_fallido,
    registrar_login_exitoso,
    verify_password,
)
from ..database import get_db
from ..models import Usuario
from ..utils import add_flash, pop_flashes, templates

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"usuario": None, "flashes": pop_flashes(request)},
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.email == email.strip().lower()).first()

    if usuario and esta_bloqueado(usuario):
        add_flash(
            request,
            "Esta cuenta está bloqueada temporalmente por demasiados intentos fallidos. Intenta de nuevo en unos minutos.",
            "error",
        )
        return RedirectResponse("/login", status_code=303)

    if not usuario or not verify_password(password, usuario.password_salt, usuario.password_hash):
        if usuario:
            registrar_intento_fallido(db, usuario)
        add_flash(request, "Email o contraseña incorrectos.", "error")
        return RedirectResponse("/login", status_code=303)

    registrar_login_exitoso(db, usuario)
    login_user(request, usuario)
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)
