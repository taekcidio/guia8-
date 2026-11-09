import importlib.util
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "server", Path(__file__).resolve().parents[1] / "app" / "server.py"
)
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        server.DB = Path(self.temp.name) / "test.db"
        server.init_db()

    def tearDown(self):
        self.temp.cleanup()

    def create_user(self, email="ana@example.com"):
        status, user = server.execute(
            "POST", "/api/users", {"name": "Ana Gómez", "email": email}
        )
        self.assertEqual(status, 201)
        return user["id"]

    def test_health_and_catalog_metadata(self):
        self.assertEqual(server.execute("GET", "/api/health")[0], 200)
        status, response = server.execute("GET", "/api/products")
        self.assertEqual(status, 200)
        self.assertEqual(len(response["products"]), 4)
        self.assertEqual(response["products"][0]["category"], "Calzado")
        self.assertTrue(response["products"][0]["image"].startswith("/static/"))

    def test_user_registration_normalizes_email_and_prevents_duplicates(self):
        status, user = server.execute(
            "POST",
            "/api/users",
            {"name": "  Ana Gómez  ", "email": " Ana@Example.com "},
        )
        self.assertEqual(status, 201)
        self.assertEqual(user["name"], "Ana Gómez")
        self.assertEqual(user["email"], "ana@example.com")
        self.assertEqual(
            server.execute(
                "POST",
                "/api/users",
                {"name": "Ana", "email": "ana@example.com"},
            )[0],
            409,
        )

    def test_registration_rejects_invalid_fields(self):
        invalid_users = [
            {"name": "", "email": "bad"},
            {"name": "Ana", "email": "ana@"},
            {"name": "A" * 81, "email": "ana@example.com"},
            {"name": "Ana", "email": "ana\n@example.com"},
        ]
        for payload in invalid_users:
            with self.subTest(payload=payload):
                self.assertEqual(server.execute("POST", "/api/users", payload)[0], 400)

    def test_order_records_details_and_updates_inventory(self):
        user_id = self.create_user()
        status, order = server.execute(
            "POST",
            "/api/orders",
            {"user_id": user_id, "items": [{"product_id": 1, "quantity": 2}]},
        )
        self.assertEqual(status, 201)
        self.assertEqual(order["total"], 439800)
        self.assertEqual(order["status"], "Pendiente de pago")
        self.assertEqual(
            server.execute("GET", "/api/inventory")[1]["inventory"][0]["stock"], 10
        )
        stored_order = server.execute("GET", "/api/orders")[1]["orders"][0]
        self.assertEqual(stored_order["user_name"], "Ana Gómez")
        self.assertEqual(stored_order["items"][0]["product_name"], "Tenis para running")
        self.assertEqual(stored_order["items"][0]["quantity"], 2)
        self.assertNotEqual(stored_order["status"], "registrado_sin_pago")

    def test_insufficient_stock_does_not_create_order_or_decrease_inventory(self):
        user_id = self.create_user()
        status, result = server.execute(
            "POST",
            "/api/orders",
            {"user_id": user_id, "items": [{"product_id": 1, "quantity": 13}]},
        )
        self.assertEqual(status, 409)
        self.assertIn("Solo quedan 12", result["error"])
        self.assertEqual(server.execute("GET", "/api/orders")[1]["orders"], [])
        self.assertEqual(
            server.execute("GET", "/api/inventory")[1]["inventory"][0]["stock"], 12
        )

    def test_duplicate_order_lines_are_combined_before_stock_check(self):
        user_id = self.create_user()
        status, _ = server.execute(
            "POST",
            "/api/orders",
            {
                "user_id": user_id,
                "items": [
                    {"product_id": 1, "quantity": 7},
                    {"product_id": 1, "quantity": 6},
                ],
            },
        )
        self.assertEqual(status, 409)
        self.assertEqual(server.execute("GET", "/api/orders")[1]["orders"], [])

    def test_concurrent_orders_cannot_overdraw_inventory(self):
        user_id = self.create_user()

        def place_order():
            return server.execute(
                "POST",
                "/api/orders",
                {"user_id": user_id, "items": [{"product_id": 1, "quantity": 8}]},
            )[0]

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(lambda _: place_order(), range(2)))

        self.assertCountEqual(statuses, [201, 409])
        self.assertEqual(
            server.execute("GET", "/api/inventory")[1]["inventory"][0]["stock"], 4
        )
        self.assertEqual(len(server.execute("GET", "/api/orders")[1]["orders"]), 1)

    def test_legacy_order_status_is_shown_in_plain_language(self):
        user_id = self.create_user()
        status, order = server.execute(
            "POST",
            "/api/orders",
            {"user_id": user_id, "items": [{"product_id": 2, "quantity": 1}]},
        )
        self.assertEqual(status, 201)
        with server.connection_scope() as connection:
            connection.execute(
                "UPDATE orders SET status=? WHERE id=?",
                ("registrado_sin_pago", order["id"]),
            )
        stored_order = server.execute("GET", "/api/orders")[1]["orders"][0]
        self.assertEqual(stored_order["status"], "Pendiente de pago")

    def test_order_rejects_invalid_quantity_and_user(self):
        for quantity in (0, -1, True, 1001):
            with self.subTest(quantity=quantity):
                status, _ = server.execute(
                    "POST",
                    "/api/orders",
                    {
                        "user_id": 999,
                        "items": [{"product_id": 1, "quantity": quantity}],
                    },
                )
                self.assertEqual(status, 400)
        user_id = self.create_user()
        self.assertEqual(
            server.execute(
                "POST",
                "/api/orders",
                {"user_id": user_id, "items": [{"product_id": 999, "quantity": 1}]},
            )[0],
            404,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
