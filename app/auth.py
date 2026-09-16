"""Autenticación por sesión, hashing de contraseñas y control de acceso por rol."""
import datetime
import hashlib
import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette import status

from .database import get_db
from .models import RolUsuario, Usuario

MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 5


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return digest.hex(), salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    digest, _ = hash_password(password, salt)
    return secrets.compare_digest(digest, password_hash)


def login_user(request: Request, usuario: Usuario) -> None:
    request.session["user_id"] = usuario.id


def logout_user(request: Request) -> None:
    request.session.clear()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(Usuario, user_id)


def _redirect_to_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_303_SEE_OTHER,
        headers={"Location": "/login"},
    )


def require_login(
    request: Request, db: Session = Depends(get_db)
) -> Usuario:
    usuario = get_current_user(request, db)
    if usuario is None:
        raise _redirect_to_login()
    return usuario


def require_admin(
    request: Request, db: Session = Depends(get_db)
) -> Usuario:
    usuario = require_login(request, db)
    if usuario.rol != RolUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: esta sección es solo para administradores.",
        )
    return usuario


def registrar_intento_fallido(db: Session, usuario: Usuario) -> None:
    usuario.intentos_fallidos += 1
    if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
        usuario.bloqueado_hasta = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=MINUTOS_BLOQUEO
        )
    db.commit()


def registrar_login_exitoso(db: Session, usuario: Usuario) -> None:
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()


def esta_bloqueado(usuario: Usuario) -> bool:
    if not usuario.bloqueado_hasta:
        return False
    if usuario.bloqueado_hasta <= datetime.datetime.utcnow():
        return False
    return True
