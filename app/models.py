"""Modelos SQLAlchemy: Categoria, Proveedor, Producto, Movimiento, Usuario."""
import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    OPERADOR = "operador"


class TipoMovimiento(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), unique=True, nullable=False, index=True)
    descripcion = Column(Text, nullable=True)

    productos = relationship("Producto", back_populates="categoria")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    contacto = Column(String(150), nullable=True)
    telefono = Column(String(40), nullable=True)
    email = Column(String(150), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    productos = relationship("Producto", back_populates="proveedor")


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (UniqueConstraint("sku", name="uq_producto_sku"),)

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    sku = Column(String(60), nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    precio = Column(Float, nullable=False)
    stock_actual = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=0, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    categoria = relationship("Categoria", back_populates="productos")
    proveedor = relationship("Proveedor", back_populates="productos")
    movimientos = relationship(
        "Movimiento", back_populates="producto", order_by="Movimiento.fecha"
    )

    @property
    def stock_bajo(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    @property
    def valor_total(self) -> float:
        return round(self.stock_actual * self.precio, 2)


class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    tipo = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Integer, nullable=False)
    motivo = Column(String(255), nullable=False)
    fecha = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    saldo_resultante = Column(Integer, nullable=False)

    producto = relationship("Producto", back_populates="movimientos")
    usuario = relationship("Usuario")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(64), nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.OPERADOR)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime, nullable=True)
