"""Acciones administrativas de conveniencia.

No corresponde a ningún PBI del backlog: existe porque en el plan gratuito de Render
no hay acceso a Shell, así que esta es la forma de cargar los datos de ejemplo (o
recargarlos tras un reinicio, ya que en el plan gratuito el almacenamiento es efímero)
sin necesitar una terminal.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..models import Producto
from ..seed_demo import run as ejecutar_seed_demo
from ..utils import add_flash

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed-demo")
def cargar_datos_demo(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    antes = db.query(Producto).count()
    ejecutar_seed_demo()
    db.expire_all()
    despues = db.query(Producto).count()

    if despues > antes:
        add_flash(
            request,
            f"Datos de ejemplo cargados correctamente ({despues} productos en total).",
        )
    else:
        add_flash(
            request,
            "Ya había productos en el sistema; no se cargaron datos de ejemplo para evitar duplicados.",
            "info",
        )
    return RedirectResponse("/", status_code=303)