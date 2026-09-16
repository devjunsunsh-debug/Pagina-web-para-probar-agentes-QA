"""Reporte de Inventario Exportable (PBI 7)."""
import csv
import io

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import require_login
from ..database import get_db
from ..models import Categoria, Producto, Proveedor
from ..utils import pop_flashes, templates

router = APIRouter(prefix="/reportes", tags=["reportes"])


def _productos_filtrados(db: Session, categoria_id: str, proveedor_id: str):
    query = db.query(Producto).filter(Producto.activo.is_(True))
    if categoria_id:
        query = query.filter(Producto.categoria_id == int(categoria_id))
    if proveedor_id:
        query = query.filter(Producto.proveedor_id == int(proveedor_id))
    return query.order_by(Producto.nombre.asc()).all()


@router.get("")
def reporte(
    request: Request,
    categoria_id: str = "",
    proveedor_id: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    productos = _productos_filtrados(db, categoria_id, proveedor_id)
    valor_total = sum(p.valor_total for p in productos)
    categorias = db.query(Categoria).order_by(Categoria.nombre.asc()).all()
    proveedores = db.query(Proveedor).order_by(Proveedor.nombre.asc()).all()

    return templates.TemplateResponse(
        request,
        "reportes.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "productos": productos,
            "valor_total": valor_total,
            "categorias": categorias,
            "proveedores": proveedores,
            "categoria_id": categoria_id,
            "proveedor_id": proveedor_id,
        },
    )


@router.get("/exportar")
def exportar_csv(
    categoria_id: str = "",
    proveedor_id: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    productos = _productos_filtrados(db, categoria_id, proveedor_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Producto", "SKU", "Categoria", "Proveedor", "Stock actual", "Stock minimo", "Precio", "Valor total"]
    )
    for p in productos:
        writer.writerow(
            [p.nombre, p.sku, p.categoria.nombre, p.proveedor.nombre, p.stock_actual, p.stock_minimo, p.precio, p.valor_total]
        )
    valor_total = sum(p.valor_total for p in productos)
    writer.writerow([])
    writer.writerow(["", "", "", "", "", "", "Total:", valor_total])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_inventario.csv"},
    )
