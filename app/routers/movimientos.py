"""Registrar Movimientos de Stock — Entradas y Salidas (PBI 4)."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import require_login
from ..database import get_db
from ..models import Movimiento, Producto, TipoMovimiento
from ..utils import add_flash, pop_flashes, templates

router = APIRouter(prefix="/movimientos", tags=["movimientos"])


@router.get("/nuevo")
def nuevo_form(
    request: Request,
    producto_id: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    productos = (
        db.query(Producto)
        .filter(Producto.activo.is_(True))
        .order_by(Producto.nombre.asc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "movimientos/nuevo.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "productos": productos,
            "producto_id": producto_id,
        },
    )


@router.post("/nuevo")
def crear(
    request: Request,
    producto_id: int = Form(...),
    tipo: str = Form(...),
    cantidad: str = Form(...),
    motivo: str = Form(...),
    volver_a: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    destino = volver_a or "/movimientos/nuevo"
    producto = db.get(Producto, producto_id)
    if not producto:
        add_flash(request, "Producto no encontrado.", "error")
        return RedirectResponse(destino, status_code=303)

    motivo = motivo.strip()
    if not motivo:
        add_flash(request, "El motivo del movimiento es obligatorio.", "error")
        return RedirectResponse(destino, status_code=303)

    if tipo not in (TipoMovimiento.ENTRADA.value, TipoMovimiento.SALIDA.value):
        add_flash(request, "Tipo de movimiento inválido.", "error")
        return RedirectResponse(destino, status_code=303)

    try:
        cantidad_val = int(cantidad)
    except ValueError:
        add_flash(request, "La cantidad debe ser un número entero.", "error")
        return RedirectResponse(destino, status_code=303)

    if cantidad_val <= 0:
        add_flash(request, "La cantidad debe ser mayor a 0.", "error")
        return RedirectResponse(destino, status_code=303)

    if tipo == TipoMovimiento.SALIDA.value and cantidad_val > producto.stock_actual:
        add_flash(
            request,
            f"No se puede registrar la salida: stock disponible de '{producto.nombre}' es {producto.stock_actual} y se intentaron sacar {cantidad_val}.",
            "error",
        )
        return RedirectResponse(destino, status_code=303)

    if tipo == TipoMovimiento.ENTRADA.value:
        producto.stock_actual += cantidad_val
    else:
        producto.stock_actual -= cantidad_val

    movimiento = Movimiento(
        producto_id=producto.id,
        tipo=TipoMovimiento(tipo),
        cantidad=cantidad_val,
        motivo=motivo,
        usuario_id=usuario.id,
        saldo_resultante=producto.stock_actual,
    )
    db.add(movimiento)
    db.commit()
    add_flash(request, f"Movimiento de {tipo} registrado para '{producto.nombre}'. Nuevo stock: {producto.stock_actual}.")
    return RedirectResponse(destino, status_code=303)
