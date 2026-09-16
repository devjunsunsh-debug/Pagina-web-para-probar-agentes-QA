"""Gestión de Usuarios y Roles (PBI 9) — solo Administrador."""
import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import hash_password, require_admin
from ..database import get_db
from ..models import RolUsuario, Usuario
from ..utils import add_flash, pop_flashes, templates

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("")
def listar(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    usuarios = db.query(Usuario).order_by(Usuario.nombre.asc()).all()
    return templates.TemplateResponse(
        request,
        "usuarios/lista.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "usuarios": usuarios,
            "now": datetime.datetime.utcnow(),
        },
    )


@router.post("")
def crear(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    nombre = nombre.strip()
    email = email.strip().lower()

    if not nombre or not email or not password:
        add_flash(request, "Nombre, email y contraseña son obligatorios.", "error")
        return RedirectResponse("/usuarios", status_code=303)

    if len(password) < 6:
        add_flash(request, "La contraseña debe tener al menos 6 caracteres.", "error")
        return RedirectResponse("/usuarios", status_code=303)

    if rol not in (RolUsuario.ADMINISTRADOR.value, RolUsuario.OPERADOR.value):
        add_flash(request, "Rol inválido.", "error")
        return RedirectResponse("/usuarios", status_code=303)

    existente = db.query(Usuario).filter(Usuario.email == email).first()
    if existente:
        add_flash(request, f"Ya existe un usuario con el email '{email}'.", "error")
        return RedirectResponse("/usuarios", status_code=303)

    password_hash, salt = hash_password(password)
    nuevo = Usuario(
        nombre=nombre,
        email=email,
        password_hash=password_hash,
        password_salt=salt,
        rol=RolUsuario(rol),
    )
    db.add(nuevo)
    db.commit()
    add_flash(request, f"Usuario '{nombre}' creado con rol {rol}.")
    return RedirectResponse("/usuarios", status_code=303)


@router.post("/{usuario_id}/rol")
def cambiar_rol(
    request: Request,
    usuario_id: int,
    rol: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    objetivo = db.get(Usuario, usuario_id)
    if not objetivo:
        add_flash(request, "Usuario no encontrado.", "error")
        return RedirectResponse("/usuarios", status_code=303)
    if rol not in (RolUsuario.ADMINISTRADOR.value, RolUsuario.OPERADOR.value):
        add_flash(request, "Rol inválido.", "error")
        return RedirectResponse("/usuarios", status_code=303)

    objetivo.rol = RolUsuario(rol)
    db.commit()
    add_flash(request, f"Rol de '{objetivo.nombre}' actualizado a {rol}.")
    return RedirectResponse("/usuarios", status_code=303)
