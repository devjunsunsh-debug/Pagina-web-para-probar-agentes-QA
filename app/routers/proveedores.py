"""Gestión de Proveedores (PBI 2)."""
import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..models import Proveedor
from ..utils import add_flash, pop_flashes, templates

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.get("")
def listar(
    request: Request,
    q: str = "",
    estado: str = "todos",
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    query = db.query(Proveedor)
    if q:
        query = query.filter(Proveedor.nombre.ilike(f"%{q}%"))
    if estado == "activos":
        query = query.filter(Proveedor.activo.is_(True))
    elif estado == "inactivos":
        query = query.filter(Proveedor.activo.is_(False))
    proveedores = query.order_by(Proveedor.nombre.asc()).all()
    return templates.TemplateResponse(
        request,
        "proveedores/lista.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "proveedores": proveedores,
            "q": q,
            "estado": estado,
        },
    )


@router.post("")
def crear(
    request: Request,
    nombre: str = Form(...),
    contacto: str = Form(""),
    telefono: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    nombre = nombre.strip()
    email = email.strip()
    if not nombre:
        add_flash(request, "El nombre del proveedor es obligatorio.", "error")
        return RedirectResponse("/proveedores", status_code=303)
    if email and not EMAIL_RE.match(email):
        add_flash(request, f"El email '{email}' no tiene un formato válido.", "error")
        return RedirectResponse("/proveedores", status_code=303)

    proveedor = Proveedor(
        nombre=nombre,
        contacto=contacto.strip() or None,
        telefono=telefono.strip() or None,
        email=email or None,
        activo=True,
    )
    db.add(proveedor)
    db.commit()
    add_flash(request, f"Proveedor '{nombre}' creado correctamente.")
    return RedirectResponse("/proveedores", status_code=303)


@router.post("/{proveedor_id}/editar")
def editar(
    request: Request,
    proveedor_id: int,
    nombre: str = Form(...),
    contacto: str = Form(""),
    telefono: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if not proveedor:
        add_flash(request, "Proveedor no encontrado.", "error")
        return RedirectResponse("/proveedores", status_code=303)

    nombre = nombre.strip()
    email = email.strip()
    if not nombre:
        add_flash(request, "El nombre del proveedor es obligatorio.", "error")
        return RedirectResponse("/proveedores", status_code=303)
    if email and not EMAIL_RE.match(email):
        add_flash(request, f"El email '{email}' no tiene un formato válido.", "error")
        return RedirectResponse("/proveedores", status_code=303)

    proveedor.nombre = nombre
    proveedor.contacto = contacto.strip() or None
    proveedor.telefono = telefono.strip() or None
    proveedor.email = email or None
    db.commit()
    add_flash(request, "Proveedor actualizado correctamente.")
    return RedirectResponse("/proveedores", status_code=303)


@router.post("/{proveedor_id}/estado")
def cambiar_estado(
    request: Request,
    proveedor_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    proveedor = db.get(Proveedor, proveedor_id)
    if not proveedor:
        add_flash(request, "Proveedor no encontrado.", "error")
        return RedirectResponse("/proveedores", status_code=303)

    proveedor.activo = not proveedor.activo
    db.commit()
    estado = "activado" if proveedor.activo else "desactivado"
    add_flash(request, f"Proveedor '{proveedor.nombre}' {estado} correctamente.")
    return RedirectResponse("/proveedores", status_code=303)
