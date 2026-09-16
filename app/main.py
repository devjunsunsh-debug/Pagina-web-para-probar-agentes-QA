"""Sistema de Inventario — punto de entrada de la aplicación FastAPI.

Aplicación de prueba (no pertenece a ninguna empresa real) construida para validar
agentes QA: generación de test cases en Azure DevOps, ejecución con Playwright y
generación de manuales de usuario a partir de capturas de pantalla.
"""
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import hash_password
from .database import Base, SessionLocal, engine, get_db
from .models import RolUsuario, Usuario
from .routers import (
    auth_routes,
    busqueda,
    categorias,
    dashboard,
    movimientos,
    productos,
    proveedores,
    reportes,
    usuarios,
)
from .utils import templates

APP_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")
if SECRET_KEY == "dev-secret-key-cambiar-en-produccion":
    print(
        "[ADVERTENCIA] Usando SECRET_KEY de desarrollo. "
        "Define la variable de entorno SECRET_KEY antes de desplegar a producción."
    )

app = FastAPI(title="Sistema de Inventario")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax")
app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")

app.include_router(auth_routes.router)
app.include_router(dashboard.router)
app.include_router(categorias.router)
app.include_router(proveedores.router)
app.include_router(productos.router)
app.include_router(movimientos.router)
app.include_router(reportes.router)
app.include_router(usuarios.router)
app.include_router(busqueda.router)


DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@inventario.local")
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123!")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Usuario).count() == 0:
            password_hash, salt = hash_password(DEFAULT_ADMIN_PASSWORD)
            admin = Usuario(
                nombre="Administrador",
                email=DEFAULT_ADMIN_EMAIL,
                password_hash=password_hash,
                password_salt=salt,
                rol=RolUsuario.ADMINISTRADOR,
            )
            db.add(admin)
            db.commit()
            print(
                f"[SETUP] Usuario administrador creado: {DEFAULT_ADMIN_EMAIL} / "
                f"{DEFAULT_ADMIN_PASSWORD} (cámbialo después de tu primer login)."
            )
    finally:
        db.close()


@app.exception_handler(403)
async def acceso_denegado_handler(request: Request, exc: HTTPException):
    from .auth import get_current_user

    db = next(get_db())
    try:
        usuario = get_current_user(request, db)
    finally:
        db.close()
    return templates.TemplateResponse(
        request,
        "acceso_denegado.html",
        {"usuario": usuario, "flashes": [], "detalle": exc.detail},
        status_code=403,
    )


@app.get("/salud")
def salud():
    """Endpoint simple para healthchecks (Render y similares)."""
    return {"status": "ok"}
