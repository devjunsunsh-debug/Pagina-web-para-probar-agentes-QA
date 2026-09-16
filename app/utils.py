"""Utilidades compartidas: instancia de templates y mensajes flash vía sesión."""
import os

from fastapi import Request
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def add_flash(request: Request, message: str, category: str = "success") -> None:
    flashes = request.session.get("flash", [])
    flashes.append({"message": message, "category": category})
    request.session["flash"] = flashes


def pop_flashes(request: Request) -> list:
    flashes = request.session.get("flash", [])
    request.session["flash"] = []
    return flashes
