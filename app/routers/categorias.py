"""Gestión de Categorías de Producto (PBI 1)."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..models import Categoria
from ..utils import add_flash, pop_flashes, templates

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("")
def listar(
    request: Request,
    q: str = "",
    orden: str = "asc",
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    query = db.query(Categoria)
    if q:
        query = query.filter(Categoria.nombre.ilike(f"%{q}%"))
    query = query.order_by(
        Categoria.nombre.asc() if orden != "desc" else Categoria.nombre.desc()
    )
    categorias = query.all()
    return templates.TemplateResponse(
        request,
        "categorias/lista.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "categorias": categorias,
            "q": q,
            "orden": orden,
        },
    )


@router.post("")
def crear(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    nombre = nombre.strip()
    if not nombre:
        add_flash(request, "El nombre de la categoría es obligatorio.", "error")
        return RedirectResponse("/categorias", status_code=303)

    existente = db.query(Categoria).filter(Categoria.nombre.ilike(nombre)).first()
    if existente:
        add_flash(request, f"Ya existe una categoría llamada '{nombre}'.", "error")
        return RedirectResponse("/categorias", status_code=303)

    categoria = Categoria(nombre=nombre, descripcion=descripcion.strip() or None)
    db.add(categoria)
    db.commit()
    add_flash(request, f"Categoría '{nombre}' creada correctamente.")
    return RedirectResponse("/categorias", status_code=303)


@router.post("/{categoria_id}/editar")
def editar(
    request: Request,
    categoria_id: int,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        add_flash(request, "Categoría no encontrada.", "error")
        return RedirectResponse("/categorias", status_code=303)

    nombre = nombre.strip()
    if not nombre:
        add_flash(request, "El nombre de la categoría es obligatorio.", "error")
        return RedirectResponse("/categorias", status_code=303)

    duplicada = (
        db.query(Categoria)
        .filter(Categoria.nombre.ilike(nombre), Categoria.id != categoria_id)
        .first()
    )
    if duplicada:
        add_flash(request, f"Ya existe otra categoría llamada '{nombre}'.", "error")
        return RedirectResponse("/categorias", status_code=303)

    categoria.nombre = nombre
    categoria.descripcion = descripcion.strip() or None
    db.commit()
    add_flash(request, "Categoría actualizada correctamente.")
    return RedirectResponse("/categorias", status_code=303)


@router.post("/{categoria_id}/eliminar")
def eliminar(
    request: Request,
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        add_flash(request, "Categoría no encontrada.", "error")
        return RedirectResponse("/categorias", status_code=303)

    if categoria.productos:
        add_flash(
            request,
            f"No se puede eliminar '{categoria.nombre}' porque tiene {len(categoria.productos)} producto(s) asociado(s).",
            "error",
        )
        return RedirectResponse("/categorias", status_code=303)

    db.delete(categoria)
    db.commit()
    add_flash(request, "Categoría eliminada correctamente.")
    return RedirectResponse("/categorias", status_code=303)
