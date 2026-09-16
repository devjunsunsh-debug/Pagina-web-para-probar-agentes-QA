"""Dashboard Principal (PBI 8) y Alertas de Stock Bajo (PBI 6)."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..auth import require_login
from ..database import get_db
from ..models import Movimiento, Producto
from ..utils import pop_flashes, templates

router = APIRouter(tags=["dashboard"])


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    productos_activos = db.query(Producto).filter(Producto.activo.is_(True)).all()
    total_productos = len(productos_activos)
    valor_total = sum(p.valor_total for p in productos_activos)
    stock_bajo = [p for p in productos_activos if p.stock_bajo]
    ultimos_movimientos = (
        db.query(Movimiento).order_by(Movimiento.fecha.desc()).limit(5).all()
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "total_productos": total_productos,
            "valor_total": valor_total,
            "stock_bajo_count": len(stock_bajo),
            "ultimos_movimientos": ultimos_movimientos,
            "hay_datos": total_productos > 0,
        },
    )


@router.get("/alertas")
def alertas(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    productos_activos = db.query(Producto).filter(Producto.activo.is_(True)).all()
    en_alerta = [p for p in productos_activos if p.stock_bajo]
    en_alerta.sort(key=lambda p: p.stock_actual - p.stock_minimo)

    return templates.TemplateResponse(
        request,
        "alertas.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "productos": en_alerta,
        },
    )
