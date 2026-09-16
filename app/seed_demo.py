"""Script opcional para poblar datos de ejemplo (no reales, solo demo/pruebas).

Uso: desde la raíz del proyecto, con el entorno virtual activado:
    python -m app.seed_demo
"""
from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import Categoria, Movimiento, Producto, Proveedor, RolUsuario, TipoMovimiento, Usuario


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Producto).count() > 0:
            print("Ya hay productos en la base de datos. No se cargaron datos de ejemplo.")
            return

        if db.query(Usuario).count() == 0:
            password_hash, salt = hash_password("Admin123!")
            admin = Usuario(
                nombre="Administrador",
                email="admin@inventario.local",
                password_hash=password_hash,
                password_salt=salt,
                rol=RolUsuario.ADMINISTRADOR,
            )
            op_pw, op_salt = hash_password("Operador123!")
            operador = Usuario(
                nombre="Operador Demo",
                email="operador@inventario.local",
                password_hash=op_pw,
                password_salt=op_salt,
                rol=RolUsuario.OPERADOR,
            )
            db.add_all([admin, operador])
            db.commit()
        else:
            admin = db.query(Usuario).filter(Usuario.rol == RolUsuario.ADMINISTRADOR).first()

        categorias = {
            "Bebidas": Categoria(nombre="Bebidas", descripcion="Bebidas frías y calientes"),
            "Abarrotes": Categoria(nombre="Abarrotes", descripcion="Productos secos y no perecederos"),
            "Aseo y limpieza": Categoria(nombre="Aseo y limpieza", descripcion="Artículos de limpieza"),
            "Papelería": Categoria(nombre="Papelería", descripcion="Insumos de oficina"),
        }
        db.add_all(categorias.values())

        proveedores = {
            "Distribuidora El Sol": Proveedor(nombre="Distribuidora El Sol", contacto="Laura Gómez", telefono="3001234567", email="ventas@elsol.example.com"),
            "Comercializadora Andina": Proveedor(nombre="Comercializadora Andina", contacto="Julián Pérez", telefono="3109876543", email="contacto@andina.example.com"),
            "Suministros Rápidos": Proveedor(nombre="Suministros Rápidos", contacto="Marta Ruiz", telefono="3205551234", email="pedidos@rapidos.example.com"),
        }
        db.add_all(proveedores.values())
        db.commit()

        productos_data = [
            ("Agua embotellada 600ml", "BEB-001", "Bebidas", "Distribuidora El Sol", 2500, 10, 30),
            ("Café molido 500g", "ABA-010", "Abarrotes", "Comercializadora Andina", 15000, 5, 20),
            ("Arroz 1kg", "ABA-011", "Abarrotes", "Comercializadora Andina", 4200, 8, 25),
            ("Detergente en polvo 1kg", "ASE-020", "Aseo y limpieza", "Suministros Rápidos", 9800, 3, 15),
            ("Jabón líquido para manos 500ml", "ASE-021", "Aseo y limpieza", "Suministros Rápidos", 6500, 2, 12),
            ("Resma de papel carta", "PAP-030", "Papelería", "Distribuidora El Sol", 18000, 4, 10),
            ("Cuaderno cuadriculado 100 hojas", "PAP-031", "Papelería", "Distribuidora El Sol", 3200, 6, 20),
        ]

        productos = []
        for nombre, sku, cat, prov, precio, stock_minimo, stock_inicial in productos_data:
            p = Producto(
                nombre=nombre,
                sku=sku,
                categoria_id=categorias[cat].id,
                proveedor_id=proveedores[prov].id,
                precio=precio,
                stock_actual=0,
                stock_minimo=stock_minimo,
                activo=True,
            )
            db.add(p)
            db.flush()
            movimiento = Movimiento(
                producto_id=p.id,
                tipo=TipoMovimiento.ENTRADA,
                cantidad=stock_inicial,
                motivo="Carga inicial de inventario (datos de ejemplo)",
                usuario_id=admin.id if admin else None,
                saldo_resultante=stock_inicial,
            )
            p.stock_actual = stock_inicial
            db.add(movimiento)
            productos.append(p)

        db.commit()

        # Deja un producto deliberadamente en stock bajo para poder probar las alertas.
        cafe = next(p for p in productos if p.sku == "ABA-010")
        salida = Movimiento(
            producto_id=cafe.id,
            tipo=TipoMovimiento.SALIDA,
            cantidad=17,
            motivo="Venta de ejemplo para dejar el producto en stock bajo",
            usuario_id=admin.id if admin else None,
            saldo_resultante=cafe.stock_actual - 17,
        )
        cafe.stock_actual -= 17
        db.add(salida)
        db.commit()

        print("Datos de ejemplo cargados: 4 categorías, 3 proveedores, 7 productos, movimientos iniciales.")
        print("Usuarios demo -> admin@inventario.local / Admin123!  |  operador@inventario.local / Operador123!")
    finally:
        db.close()


if __name__ == "__main__":
    run()
