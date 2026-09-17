# Sistema de Inventario (app de prueba para agentes QA)

Aplicación web de inventario, **ficticia y sin ninguna relación con producto real**, construida como
aplicación objetivo para validar el flujo agentes QA: generación de test cases en Azure DevOps,
ejecución automática con Playwright, y (a futuro) generación de manuales de usuario a partir de capturas.

Implementa el backlog de 10 PBIs que estan creados en Azure DevOps, en el proyecto QA-Agent_Azure_Web
(`backlog-sistema-inventario.md`): categorías, proveedores, productos, movimientos de stock,
historial, alertas de stock bajo, reporte exportable, dashboard, usuarios/roles y búsqueda global.
## Stack

- FastAPI + Jinja2 (mismo patrón que QA-Agent-Web y QA-Agent-Azure-Personal)
- SQLite vía SQLAlchemy (un solo archivo `inventario.db`, no requiere servidor de base de datos aparte)
- Autenticación por sesión (cookies firmadas), sin dependencias externas de auth

## Estructura

```
sistema-inventario/
├── app/
│   ├── main.py            # arranque de la app, middlewares, manejo de errores
│   ├── database.py        # configuración de SQLAlchemy
│   ├── models.py          # Categoria, Proveedor, Producto, Movimiento, Usuario
│   ├── auth.py             # login, hashing de contraseñas, control de roles
│   ├── utils.py            # templates compartidos y mensajes flash
│   ├── seed_demo.py        # datos de ejemplo opcionales
│   ├── routers/             # un archivo por PBI/área funcional
│   └── templates/           # vistas Jinja2
├── requirements.txt
└── README.md
```

## Cómo correrlo en tu computador

1. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. (Opcional pero recomendado para probar de una vez) Carga datos de ejemplo:
   ```bash
   python -m app.seed_demo
   ```
   Esto crea 4 categorías, 3 proveedores, 7 productos con movimientos iniciales, un producto
   deliberadamente en stock bajo (para probar alertas), y dos usuarios:
   - Administrador: `admin@inventario.local` / `Admin123!`
   - Operador: `operador@inventario.local` / `Operador123!`

   Si prefieres arrancar completamente vacío, sáltate este paso: al iniciar el servidor por
   primera vez se crea automáticamente un usuario administrador con el email/contraseña que
   definas en las variables de entorno `ADMIN_EMAIL` / `ADMIN_PASSWORD` (por defecto
   `admin@inventario.local` / `Admin123!`).

4. Levanta el servidor:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Abre `http://localhost:8000` e inicia sesión con el usuario administrador.

**Cambia la contraseña del administrador por defecto** antes de exponer la app públicamente
(por ahora no hay pantalla de "cambiar mi contraseña"; la forma más rápida es crear un nuevo
usuario administrador desde la sección Usuarios y luego dejar de usar el de por defecto).

## Cómo desplegarlo en Render (para tener una URL pública)

Esto es lo que necesitas para que Playwright, desde QA-Agent-Azure-Web, tenga una URL pública
real contra la cual ejecutar los test cases — igual que hiciste con tus otros proyectos.

1. Sube esta carpeta a un repositorio nuevo en GitHub (tal como vienes haciendo con tus otros
   proyectos, paso a paso).
2. En Render: **New +** → **Web Service** → conecta el repositorio.
3. Configuración del servicio:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Variables de entorno (pestaña **Environment**):
   - `SECRET_KEY` → genera una cadena aleatoria larga (por ejemplo con `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `ADMIN_EMAIL` y `ADMIN_PASSWORD` → opcional, si quieres definir tus propias credenciales
     iniciales en vez de las de por defecto
5. Despliega. Render te dará una URL pública tipo `https://sistema-inventario-xxxx.onrender.com`.

   **Nota sobre SQLite en Render:** el plan gratuito de Render usa almacenamiento efímero, así
   que la base de datos SQLite se reinicia en cada redeploy. Para este propósito (aplicación de
   prueba para tus agentes QA) normalmente está bien — simplemente vuelve a correr
   `python -m app.seed_demo` (o crea los datos manualmente) después de cada redeploy si necesitas
   datos de ejemplo. Si más adelante quieres persistencia real, Render ofrece discos persistentes
   o puedes migrar a una base de datos Postgres gestionada.

## Cómo conectarlo con tus agentes QA

1. En tu Azure DevOps personal ("CamiloJarvisAgent"), crea un nuevo proyecto o área para el
   Sistema de Inventario y carga los PBIs del backlog (`backlog-sistema-inventario.md`).
2. En QA-Agent-Azure-Web, genera los test cases con IA para cada PBI como ya vienes haciendo.
3. En la sección "Ejecutar test cases (Playwright)", pon como **URL base a probar** la URL pública
   de esta app (local con un túnel, o la de Render una vez desplegada) — nunca una URL que pida
   login externo que el agente no pueda resolver.
4. Usa las credenciales de administrador u operador según lo que el test case necesite probar.

## Roles

- **Administrador:** gestiona categorías, proveedores, productos, usuarios y ve reportes.
- **Operador:** registra movimientos de stock y consulta dashboard, historial y alertas (no
  puede editar el catálogo). Es una buena fuente de test cases de control de acceso.
