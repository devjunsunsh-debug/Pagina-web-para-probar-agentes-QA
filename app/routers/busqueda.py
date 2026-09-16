"""Búsqueda Global (PBI 10)."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..auth import require_login
from ..database import get_db
from ..models import Producto, Proveedor
from ..utils import pop_flashes, templates

router = APIRouter(tags=["busqueda"])


@router.get("/buscar")
def buscar(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    q = q.strip()
    productos = []
    proveedores = []
    if q:
        like = f"%{q}%"
        productos = (
            db.query(Producto)
            .filter((Producto.nombre.ilike(like)) | (Producto.sku.ilike(like)))
            .order_by(Producto.nombre.asc())
            .all()
        )
        proveedores = (
            db.query(Proveedor)
            .filter(Proveedor.nombre.ilike(like))
            .order_by(Proveedor.nombre.asc())
            .all()
        )

    return templates.TemplateResponse(
        request,
        "busqueda.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "q": q,
            "productos": productos,
            "proveedores": proveedores,
            "hay_resultados": bool(productos or proveedores),
        },
    )
