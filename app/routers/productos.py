"""Gestión de Productos — CRUD maestro-detalle (PBI 3)."""
import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import require_admin, require_login
from ..database import get_db
from ..models import Categoria, Producto, Proveedor, TipoMovimiento
from ..utils import add_flash, pop_flashes, templates

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("")
def listar(
    request: Request,
    q: str = "",
    categoria_id: str = "",
    proveedor_id: str = "",
    estado: str = "todos",
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    query = db.query(Producto)
    if q:
        like = f"%{q}%"
        query = query.filter((Producto.nombre.ilike(like)) | (Producto.sku.ilike(like)))
    if categoria_id:
        query = query.filter(Producto.categoria_id == int(categoria_id))
    if proveedor_id:
        query = query.filter(Producto.proveedor_id == int(proveedor_id))
    if estado == "activos":
        query = query.filter(Producto.activo.is_(True))
    elif estado == "inactivos":
        query = query.filter(Producto.activo.is_(False))

    productos = query.order_by(Producto.nombre.asc()).all()
    categorias = db.query(Categoria).order_by(Categoria.nombre.asc()).all()
    proveedores = db.query(Proveedor).order_by(Proveedor.nombre.asc()).all()

    return templates.TemplateResponse(
        request,
        "productos/lista.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "productos": productos,
            "categorias": categorias,
            "proveedores": proveedores,
            "q": q,
            "categoria_id": categoria_id,
            "proveedor_id": proveedor_id,
            "estado": estado,
        },
    )


@router.get("/nuevo")
def nuevo_form(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    categorias = db.query(Categoria).order_by(Categoria.nombre.asc()).all()
    proveedores = (
        db.query(Proveedor)
        .filter(Proveedor.activo.is_(True))
        .order_by(Proveedor.nombre.asc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "productos/form.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "categorias": categorias,
            "proveedores": proveedores,
            "producto": None,
        },
    )


def _validar_datos(nombre, sku, categoria_id, proveedor_id, precio, stock_minimo, db, producto_id=None):
    errores = []
    nombre = nombre.strip()
    sku = sku.strip()
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not sku:
        errores.append("El SKU es obligatorio.")
    else:
        dup_query = db.query(Producto).filter(Producto.sku.ilike(sku))
        if producto_id:
            dup_query = dup_query.filter(Producto.id != producto_id)
        if dup_query.first():
            errores.append(f"Ya existe un producto con el SKU '{sku}'.")
    if not db.get(Categoria, categoria_id):
        errores.append("La categoría seleccionada no es válida.")
    if not db.get(Proveedor, proveedor_id):
        errores.append("El proveedor seleccionado no es válido.")
    try:
        precio_val = float(precio)
        if precio_val <= 0:
            errores.append("El precio debe ser mayor a 0.")
    except (TypeError, ValueError):
        errores.append("El precio debe ser un número válido.")
    try:
        stock_minimo_val = int(stock_minimo)
        if stock_minimo_val < 0:
            errores.append("El stock mínimo no puede ser negativo.")
    except (TypeError, ValueError):
        errores.append("El stock mínimo debe ser un número entero.")
    return errores, nombre, sku


@router.post("/nuevo")
def crear(
    request: Request,
    nombre: str = Form(...),
    sku: str = Form(...),
    categoria_id: int = Form(...),
    proveedor_id: int = Form(...),
    precio: str = Form(...),
    stock_minimo: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    errores, nombre, sku = _validar_datos(nombre, sku, categoria_id, proveedor_id, precio, stock_minimo, db)
    if errores:
        for e in errores:
            add_flash(request, e, "error")
        return RedirectResponse("/productos/nuevo", status_code=303)

    producto = Producto(
        nombre=nombre,
        sku=sku,
        categoria_id=categoria_id,
        proveedor_id=proveedor_id,
        precio=float(precio),
        stock_actual=0,
        stock_minimo=int(stock_minimo),
        activo=True,
    )
    db.add(producto)
    db.commit()
    add_flash(request, f"Producto '{nombre}' creado correctamente. El stock inicia en 0; regístralo con un movimiento de entrada.")
    return RedirectResponse("/productos", status_code=303)


@router.get("/{producto_id}")
def detalle(
    request: Request,
    producto_id: int,
    fecha_desde: str = "",
    fecha_hasta: str = "",
    tipo: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(require_login),
):
    producto = db.get(Producto, producto_id)
    if not producto:
        add_flash(request, "Producto no encontrado.", "error")
        return RedirectResponse("/productos", status_code=303)

    movimientos = sorted(producto.movimientos, key=lambda m: m.fecha, reverse=True)

    if fecha_desde:
        try:
            desde = datetime.datetime.strptime(fecha_desde, "%Y-%m-%d")
            movimientos = [m for m in movimientos if m.fecha >= desde]
        except ValueError:
            pass
    if fecha_hasta:
        try:
            hasta = datetime.datetime.strptime(fecha_hasta, "%Y-%m-%d") + datetime.timedelta(days=1)
            movimientos = [m for m in movimientos if m.fecha < hasta]
        except ValueError:
            pass
    if tipo in (TipoMovimiento.ENTRADA.value, TipoMovimiento.SALIDA.value):
        movimientos = [m for m in movimientos if m.tipo.value == tipo]

    return templates.TemplateResponse(
        request,
        "productos/detalle.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "producto": producto,
            "movimientos": movimientos,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "tipo": tipo,
        },
    )


@router.get("/{producto_id}/editar")
def editar_form(
    request: Request,
    producto_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    producto = db.get(Producto, producto_id)
    if not producto:
        add_flash(request, "Producto no encontrado.", "error")
        return RedirectResponse("/productos", status_code=303)

    categorias = db.query(Categoria).order_by(Categoria.nombre.asc()).all()
    proveedores_query = db.query(Proveedor).filter(
        (Proveedor.activo.is_(True)) | (Proveedor.id == producto.proveedor_id)
    )
    proveedores = proveedores_query.order_by(Proveedor.nombre.asc()).all()

    return templates.TemplateResponse(
        request,
        "productos/form.html",
        {
            "usuario": usuario,
            "flashes": pop_flashes(request),
            "categorias": categorias,
            "proveedores": proveedores,
            "producto": producto,
        },
    )


@router.post("/{producto_id}/editar")
def editar(
    request: Request,
    producto_id: int,
    nombre: str = Form(...),
    sku: str = Form(...),
    categoria_id: int = Form(...),
    proveedor_id: int = Form(...),
    precio: str = Form(...),
    stock_minimo: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    producto = db.get(Producto, producto_id)
    if not producto:
        add_flash(request, "Producto no encontrado.", "error")
        return RedirectResponse("/productos", status_code=303)

    errores, nombre, sku = _validar_datos(
        nombre, sku, categoria_id, proveedor_id, precio, stock_minimo, db, producto_id=producto_id
    )
    if errores:
        for e in errores:
            add_flash(request, e, "error")
        return RedirectResponse(f"/productos/{producto_id}/editar", status_code=303)

    producto.nombre = nombre
    producto.sku = sku
    producto.categoria_id = categoria_id
    producto.proveedor_id = proveedor_id
    producto.precio = float(precio)
    producto.stock_minimo = int(stock_minimo)
    # stock_actual es de solo lectura aquí: no se modifica desde este formulario.
    db.commit()
    add_flash(request, "Producto actualizado correctamente.")
    return RedirectResponse("/productos", status_code=303)


@router.post("/{producto_id}/eliminar")
def eliminar(
    request: Request,
    producto_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(require_admin),
):
    producto = db.get(Producto, producto_id)
    if not producto:
        add_flash(request, "Producto no encontrado.", "error")
        return RedirectResponse("/productos", status_code=303)

    if producto.movimientos:
        producto.activo = False
        db.commit()
        add_flash(
            request,
            f"'{producto.nombre}' tiene movimientos de stock registrados, así que no se puede eliminar; se desactivó en su lugar.",
            "info",
        )
        return RedirectResponse("/productos", status_code=303)

    db.delete(producto)
    db.commit()
    add_flash(request, "Producto eliminado correctamente.")
    return RedirectResponse("/productos", status_code=303)
