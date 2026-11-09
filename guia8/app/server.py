"""Servidor local de La Tiendita. No autentica ni procesa pagos reales."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
import re
import sqlite3
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB = Path(os.getenv("DATABASE_PATH", str(ROOT.parent / "data" / "comercio.db")))
DB.parent.mkdir(parents=True, exist_ok=True)
LOCK = threading.RLock()
START = time.time()
PRODUCTS = [
    (1, "Tenis para running", 219900, 12),
    (2, "Botella térmica", 45900, 25),
    (3, "Mochila deportiva", 129900, 8),
    (4, "Banda de resistencia", 34900, 30),
]
PRODUCT_DETAILS = {
    1: {
        "category": "Calzado",
        "description": "Comodidad y soporte para tus recorridos diarios.",
        "image": "/static/images/productos/tenis-running.jpg",
        "image_alt": "Tenis deportivos para correr",
    },
    2: {
        "category": "Accesorios",
        "description": "Mantén tu bebida a la temperatura ideal durante el día.",
        "image": "/static/images/productos/botella-termica.jpg",
        "image_alt": "Botella reutilizable para hidratarte",
    },
    3: {
        "category": "Accesorios",
        "description": "Espacio práctico para llevar lo necesario a entrenar.",
        "image": "/static/images/productos/mochila-deportiva.jpg",
        "image_alt": "Mochila para actividades al aire libre",
    },
    4: {
        "category": "Entrenamiento",
        "description": "Una opción versátil para sumar resistencia a tu rutina.",
        "image": "/static/images/productos/banda-resistencia.jpg",
        "image_alt": "Persona entrenando con una banda de resistencia",
    },
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LEGACY_ASSETS = {
    "/style.css": STATIC / "css" / "style.css",
    "/main.js": STATIC / "js" / "main.js",
}


def connect():
    connection = sqlite3.connect(DB, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


@contextmanager
def connection_scope():
    connection = connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db():
    with LOCK, connection_scope() as connection:
        connection.executescript(
            """CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS products(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL CHECK(price>=0),
                stock INTEGER NOT NULL CHECK(stock>=0)
            );
            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                total INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_items(
                order_id INTEGER REFERENCES orders(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL CHECK(quantity>0),
                unit_price INTEGER NOT NULL
            );"""
        )
        connection.executemany(
            "INSERT OR IGNORE INTO products(id,name,price,stock) VALUES(?,?,?,?)",
            PRODUCTS,
        )


def _public_status(status):
    if status in ("registrado_sin_pago", "pendiente_pago", "pending_payment"):
        return "Pendiente de pago"
    return status


def execute(method, path, data=None):
    with LOCK, connection_scope() as connection:
        if path == "/api/health" and method == "GET":
            return 200, {
                "status": "ok",
                "uptime_seconds": round(time.time() - START, 2),
                "storage": "sqlite-local",
            }
        if path == "/api/products" and method == "GET":
            products = []
            for row in connection.execute("SELECT * FROM products ORDER BY id"):
                product = dict(row)
                product.update(PRODUCT_DETAILS.get(product["id"], {}))
                products.append(product)
            return 200, {"products": products}
        if path == "/api/inventory" and method == "GET":
            return 200, {
                "inventory": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT id,name,stock FROM products ORDER BY id"
                    )
                ]
            }
        if path == "/api/orders" and method == "GET":
            orders = []
            rows = connection.execute(
                """SELECT o.id, o.user_id, u.name AS user_name, u.email,
                          o.total, o.status, o.created_at, oi.product_id,
                          p.name AS product_name, oi.quantity, oi.unit_price
                   FROM (SELECT * FROM orders ORDER BY id DESC LIMIT 30) o
                   JOIN users u ON u.id=o.user_id
                   LEFT JOIN order_items oi ON oi.order_id=o.id
                   LEFT JOIN products p ON p.id=oi.product_id
                   ORDER BY o.id DESC, p.name"""
            )
            for row in rows:
                order = next(
                    (item for item in orders if item["id"] == row["id"]), None
                )
                if order is None:
                    order = {
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "user_name": row["user_name"],
                        "email": row["email"],
                        "total": row["total"],
                        "status": _public_status(row["status"]),
                        "created_at": row["created_at"],
                        "items": [],
                    }
                    orders.append(order)
                if row["product_id"] is not None:
                    order["items"].append(
                        {
                            "product_id": row["product_id"],
                            "product_name": row["product_name"],
                            "quantity": row["quantity"],
                            "unit_price": row["unit_price"],
                        }
                    )
            return 200, {"orders": orders[:30]}
        if path == "/api/users" and method == "GET":
            return 200, {
                "users": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM users ORDER BY id"
                    )
                ]
            }
        if method == "POST" and path == "/api/users":
            payload = data or {}
            name = payload.get("name")
            email = payload.get("email")
            if not isinstance(name, str) or not isinstance(email, str):
                return 400, {"error": "Escribe un nombre y un correo válidos."}
            name = name.strip()
            email = email.strip().lower()
            if (
                not name
                or len(name) > 80
                or len(email) > 200
                or not EMAIL_PATTERN.fullmatch(email)
            ):
                return 400, {
                    "error": "Revisa el nombre y escribe un correo válido."
                }
            try:
                cursor = connection.execute(
                    "INSERT INTO users(name,email) VALUES(?,?)", (name, email)
                )
            except sqlite3.IntegrityError:
                return 409, {"error": "Este correo ya tiene una cuenta registrada."}
            return 201, {
                "id": cursor.lastrowid,
                "name": name,
                "email": email,
            }
        if method == "POST" and path == "/api/orders":
            payload = data or {}
            user_id = payload.get("user_id")
            items = payload.get("items")
            if type(user_id) is not int or not isinstance(items, list) or not items:
                return 400, {
                    "error": "Selecciona un usuario y al menos un producto."
                }
            merged = {}
            for item in items:
                if (
                    not isinstance(item, dict)
                    or type(item.get("product_id")) is not int
                    or type(item.get("quantity")) is not int
                    or item["quantity"] < 1
                ):
                    return 400, {"error": "Revisa el producto y la cantidad."}
                product_id = item["product_id"]
                merged[product_id] = merged.get(product_id, 0) + item["quantity"]
                if merged[product_id] > 1000:
                    return 400, {"error": "La cantidad solicitada no es válida."}

            connection.execute("BEGIN IMMEDIATE")
            if not connection.execute(
                "SELECT id FROM users WHERE id=?", (user_id,)
            ).fetchone():
                return 404, {"error": "No encontramos el usuario seleccionado."}

            details = []
            total = 0
            for product_id, quantity in merged.items():
                product = connection.execute(
                    "SELECT id,name,price,stock FROM products WHERE id=?",
                    (product_id,),
                ).fetchone()
                if product is None:
                    return 404, {"error": "No encontramos uno de los productos."}
                if product["stock"] < quantity:
                    return 409, {
                        "error": (
                            f"Solo quedan {product['stock']} unidades de "
                            f"{product['name']}."
                        )
                    }
                details.append((product_id, quantity, product["price"]))
                total += quantity * product["price"]

            cursor = connection.execute(
                "INSERT INTO orders(user_id,total,status) VALUES(?,?,?)",
                (user_id, total, "pendiente_pago"),
            )
            order_id = cursor.lastrowid
            for product_id, quantity, unit_price in details:
                connection.execute(
                    """INSERT INTO order_items(order_id,product_id,quantity,unit_price)
                       VALUES(?,?,?,?)""",
                    (order_id, product_id, quantity, unit_price),
                )
                result = connection.execute(
                    "UPDATE products SET stock=stock-? WHERE id=? AND stock>=?",
                    (quantity, product_id, quantity),
                )
                if result.rowcount != 1:
                    raise sqlite3.IntegrityError("El inventario cambió durante el pedido")
            return 201, {
                "id": order_id,
                "total": total,
                "status": "Pendiente de pago",
            }
        return 404, {"error": "No encontramos esa ruta."}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self'; "
            "object-src 'none'; base-uri 'self'",
        )
        self.end_headers()
        self.wfile.write(raw)

    def serve_file(self, file_path):
        raw = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        if content_type.startswith(("text/", "application/javascript")):
            content_type = f"{content_type}; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            return self.serve_file(ROOT / "index.html")
        if path in LEGACY_ASSETS:
            return self.serve_file(LEGACY_ASSETS[path])
        if path.startswith("/static/") and "\\" not in path:
            requested = STATIC.joinpath(*Path(path.removeprefix("/static/")).parts).resolve()
            try:
                requested.relative_to(STATIC.resolve())
            except ValueError:
                return self.respond(404, {"error": "No encontramos ese recurso."})
            if requested.is_file():
                return self.serve_file(requested)
            return self.respond(404, {"error": "No encontramos ese recurso."})
        try:
            status, result = execute("GET", path)
            return self.respond(status, result)
        except sqlite3.Error:
            print(json.dumps({"event": "database_error", "path": path}), flush=True)
            return self.respond(500, {"error": "No fue posible consultar los datos."})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 32768:
                return self.respond(413, {"error": "La solicitud está vacía o es muy grande."})
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(data, dict):
                return self.respond(400, {"error": "La solicitud debe ser un objeto JSON."})
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, {"error": "No pudimos leer la solicitud. Inténtalo de nuevo."})
        try:
            status, result = execute("POST", path, data)
            return self.respond(status, result)
        except sqlite3.Error:
            print(json.dumps({"event": "database_error", "path": path}), flush=True)
            return self.respond(500, {"error": "No fue posible guardar los datos. Inténtalo de nuevo."})

    def log_message(self, fmt, *args):
        print(
            json.dumps(
                {
                    "event": "http_request",
                    "message": fmt % args,
                    "ts": int(time.time()),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "8080"))
    print(f"La Tiendita disponible en http://0.0.0.0:{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
