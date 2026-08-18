# ty: ignore

from decimal import Decimal
from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from catalog.models import Material, MaterialCategory, Unit
from iam.models import User
from supplier.models import Supplier
from warehouse.models import Warehouse

from .models import InboundNote, StockMovement


class InventoryTestCase(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="Admin123!",
            role="admin",
            first_name="Admin",
            last_name="Test",
        )
        self.storekeeper = User.objects.create_user(
            email="thukho@test.com",
            password="Thukho123!",
            role="storekeeper",
            first_name="Thu",
            last_name="Kho",
        )
        self.accountant = User.objects.create_user(
            email="ketoan@test.com",
            password="Ketoan123!",
            role="accountant",
            first_name="Ke",
            last_name="Toan",
        )

        self.warehouse = Warehouse.objects.create(code="KHO_TEST", name="Kho test")
        self.supplier = Supplier.objects.create(
            code="NCC_TEST", name="NCC test", tax_code="9999999999"
        )
        self.category = MaterialCategory.objects.create(
            code="CAT_TEST", name="Danh mục test"
        )
        self.unit = Unit.objects.create(code="BAO", name="Bao")
        self.material = Material.objects.create(
            code="XM_TEST",
            name="Xi măng test",
            category=self.category,
            unit=self.unit,
        )
        self.material_2 = Material.objects.create(
            code="CAT_TEST_2",
            name="Cát test",
            category=self.category,
            unit=self.unit,
        )

    def _login(self, email: str, password: str) -> str:
        response: Response = self.client.post(
            "/api/auth/login/", {"email": email, "password": password}
        )
        return response.data["access"]  # type: ignore[no-any-return]

    def _note_payload(self, **overrides) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "note_type": "purchase",
            "date": "2026-08-13",
            "warehouse_id": self.warehouse.id,
            "supplier_id": self.supplier.id,
            "note": "Phiếu test",
            "lines": [
                {
                    "material_id": self.material.id,
                    "quantity": "100",
                    "unit_price": "88000",
                    "note": "",
                },
            ],
        }
        payload.update(overrides)
        return payload

    def _create_note(self, user: User, **overrides) -> dict[str, Any]:
        token = self._login(user.email, self._password_of(user))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/inbound-notes/", self._note_payload(**overrides), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data  # type: ignore[no-any-return]

    @staticmethod
    def _password_of(user: User) -> str:
        if user.email == "admin@test.com":
            return "Admin123!"
        if user.email == "thukho@test.com":
            return "Thukho123!"
        return "Ketoan123!"


class InboundNoteAPITestCase(InventoryTestCase):
    # ---------- GET list ----------

    def test_list_unauthenticated(self):
        response: Response = self.client.get("/api/inbound-notes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.get("/api/inbound-notes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---------- POST (create draft) ----------

    def test_create_draft_storekeeper(self):
        data = self._create_note(self.storekeeper)
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["number"], "PN-20260813-001")
        self.assertEqual(data["total_amount"], "8800000.00")
        self.assertEqual(data["total_quantity"], 1)  # số dòng vật tư
        self.assertEqual(data["lines"][0]["material"]["code"], "XM_TEST")
        self.assertEqual(data["lines"][0]["line_no"], 1)
        # Draft chưa có dòng sổ kho
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_number_sequence_increments(self):
        first = self._create_note(self.storekeeper)
        second = self._create_note(self.storekeeper)
        self.assertEqual(first["number"], "PN-20260813-001")
        self.assertEqual(second["number"], "PN-20260813-002")

    def test_create_accountant_forbidden(self):
        token = self._login("ketoan@test.com", "Ketoan123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/inbound-notes/", self._note_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_purchase_without_supplier(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/inbound-notes/",
            self._note_payload(supplier_id=None),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fields", response.data)

    def test_create_return_with_supplier(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/inbound-notes/",
            self._note_payload(note_type="return_from_site"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_lines(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = self._note_payload()
        payload["lines"] = []
        response: Response = self.client.post(
            "/api/inbound-notes/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_zero_quantity(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = self._note_payload()
        payload["lines"][0]["quantity"] = "0"
        response: Response = self.client.post(
            "/api/inbound-notes/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_negative_price(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = self._note_payload()
        payload["lines"][0]["unit_price"] = "-100"
        response: Response = self.client.post(
            "/api/inbound-notes/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- GET detail ----------

    def test_detail_with_lines(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        response: Response = self.client.get(f"/api/inbound-notes/{note_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lines"][0]["quantity"], "100.000")  # type: ignore[index]
        self.assertEqual(response.data["created_by"]["email"], "thukho@test.com")  # type: ignore[index]

    # ---------- PUT ----------

    def test_update_draft_replace_lines(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        payload = self._note_payload()
        payload["lines"] = [
            {
                "material_id": self.material_2.id,
                "quantity": "5.5",
                "unit_price": "350000",
                "note": "dòng mới",
            },
        ]
        response: Response = self.client.put(
            f"/api/inbound-notes/{note_id}/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["lines"]), 1)  # type: ignore[arg-type]
        self.assertEqual(response.data["lines"][0]["material"]["code"], "CAT_TEST_2")  # type: ignore[index]
        self.assertEqual(response.data["lines"][0]["line_no"], 1)  # type: ignore[index]

    def test_update_posted_forbidden(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        response: Response = self.client.post(f"/api/inbound-notes/{note_id}/post/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(
            f"/api/inbound-notes/{note_id}/",
            self._note_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- POST /post/ (chốt) ----------

    def test_post_note_creates_stock_movements(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        response: Response = self.client.post(f"/api/inbound-notes/{note_id}/post/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "posted")  # type: ignore[index]

        note = InboundNote.objects.get(id=note_id)
        self.assertEqual(note.status, "posted")
        movements = note.stock_movements.all()
        self.assertEqual(movements.count(), 1)
        movement = movements.first()
        assert movement is not None
        self.assertEqual(
            movement.movement_type,
            StockMovement.Type.INBOUND_PURCHASE_FROM_SUPPLIER,
        )
        self.assertEqual(movement.quantity, Decimal("100.000"))
        self.assertEqual(movement.unit_price, Decimal("88000.00"))
        self.assertEqual(str(movement.date), "2026-08-13")
        self.assertEqual(movement.created_by, self.storekeeper)

    def test_post_twice_forbidden(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        self.client.post(f"/api/inbound-notes/{note_id}/post/")
        response: Response = self.client.post(f"/api/inbound-notes/{note_id}/post/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- POST /void/ (hủy) ----------

    def test_void_without_reason(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        self.client.post(f"/api/inbound-notes/{note_id}/post/")
        response: Response = self.client.post(
            f"/api/inbound-notes/{note_id}/void/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_void_posted_note(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        self.client.post(f"/api/inbound-notes/{note_id}/post/")
        response: Response = self.client.post(
            f"/api/inbound-notes/{note_id}/void/",
            {"reason": "Nhập sai số lượng"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "voided")  # type: ignore[index]
        self.assertEqual(response.data["void_reason"], "Nhập sai số lượng")  # type: ignore[index]
        self.assertEqual(response.data["voided_by"]["email"], "thukho@test.com")  # type: ignore[index]

        note = InboundNote.objects.get(id=note_id)
        original = note.stock_movements.get(reversal_of__isnull=True)
        reversal = note.stock_movements.get(reversal_of=original)
        self.assertEqual(reversal.quantity, Decimal("-100.000"))
        self.assertEqual(reversal.reason, "Nhập sai số lượng")

    def test_void_draft_forbidden(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        response: Response = self.client.post(
            f"/api/inbound-notes/{note_id}/void/",
            {"reason": "hủy nháp"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- DELETE ----------

    def test_delete_draft(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        response: Response = self.client.delete(f"/api/inbound-notes/{note_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(InboundNote.objects.filter(id=note_id).exists())

    def test_delete_posted_forbidden(self):
        data = self._create_note(self.storekeeper)
        note_id = data["id"]
        self.client.post(f"/api/inbound-notes/{note_id}/post/")
        response: Response = self.client.delete(f"/api/inbound-notes/{note_id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StockAPITestCase(InventoryTestCase):
    def _post_note(self, **overrides) -> dict[str, Any]:
        data = self._create_note(self.storekeeper, **overrides)
        response: Response = self.client.post(f"/api/inbound-notes/{data['id']}/post/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return data  # type: ignore[no-any-return]

    # ---------- /api/stock/ ----------

    def test_stock_unauthenticated(self):
        response: Response = self.client.get("/api/stock/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stock_balance_after_post(self):
        self._post_note()
        response: Response = self.client.get("/api/stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = response.data  # type: ignore[assignment]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["material"]["code"], "XM_TEST")
        self.assertEqual(row["warehouse"]["code"], "KHO_TEST")
        self.assertEqual(row["unit"]["code"], "BAO")
        self.assertEqual(row["quantity"], "100.000")
        self.assertEqual(row["last_purchase_price"], "88000.00")
        self.assertEqual(row["stock_value"], "8800000.00")

    def test_draft_note_does_not_affect_stock(self):
        self._create_note(self.storekeeper)
        response: Response = self.client.get("/api/stock/")
        self.assertEqual(response.data, [])  # type: ignore[comparison-overlap]

    def test_return_note_does_not_set_last_price(self):
        self._post_note(note_type="return_from_site", supplier_id=None)
        response: Response = self.client.get("/api/stock/")
        row = response.data[0]  # type: ignore[index]
        self.assertEqual(row["quantity"], "100.000")
        self.assertIsNone(row["last_purchase_price"])
        self.assertIsNone(row["stock_value"])

    def test_void_restores_stock_to_zero(self):
        data = self._post_note()
        response: Response = self.client.post(
            f"/api/inbound-notes/{data['id']}/void/",
            {"reason": "hủy test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/stock/")
        row = response.data[0]  # type: ignore[index]
        self.assertEqual(row["quantity"], "0.000")
        self.assertEqual(row["last_purchase_price"], "88000.00")

    def test_stock_filter_has_stock(self):
        self._post_note()
        response: Response = self.client.get("/api/stock/?has_stock=true")
        self.assertEqual(len(response.data), 1)  # type: ignore[arg-type]
        response = self.client.get("/api/stock/?has_stock=false")
        self.assertEqual(len(response.data), 0)  # type: ignore[arg-type]

    # ---------- /api/stock/movements/ ----------

    def test_movements_read_only(self):
        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/stock/movements/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_movements_list_default_hides_reversals(self):
        data = self._post_note()
        self.client.post(
            f"/api/inbound-notes/{data['id']}/void/",
            {"reason": "hủy test"},
            format="json",
        )
        response: Response = self.client.get("/api/stock/movements/")
        items = response.data["items"]  # type: ignore[index]
        self.assertEqual(len(items), 1)  # chỉ dòng gốc
        self.assertEqual(items[0]["movement_type"], "inbound_purchase_from_supplier")

        response = self.client.get("/api/stock/movements/?originals_only=false")
        items = response.data["items"]  # type: ignore[index]
        self.assertEqual(len(items), 2)  # gốc + ngược dấu

    def test_movements_trace_inbound_note(self):
        data = self._post_note()
        response: Response = self.client.get("/api/stock/movements/")
        item = response.data["items"][0]  # type: ignore[index]
        self.assertEqual(item["inbound_note"]["number"], data["number"])
        self.assertEqual(
            item["movement_type_label"], "Nhập kho: mua hàng từ nhà cung cấp"
        )
        self.assertEqual(item["created_by"]["email"], "thukho@test.com")

    def test_movements_filter_by_type_and_date(self):
        self._post_note()
        response: Response = self.client.get(
            "/api/stock/movements/?movement_type=inbound_purchase_from_supplier"
        )
        self.assertEqual(len(response.data["items"]), 1)  # type: ignore[index, arg-type]

        response = self.client.get(
            "/api/stock/movements/?movement_type=inbound_return_from_site"
        )
        self.assertEqual(len(response.data["items"]), 0)  # type: ignore[index, arg-type]

        response = self.client.get(
            "/api/stock/movements/?date_from=2026-08-01&date_to=2026-08-31"
        )
        self.assertEqual(len(response.data["items"]), 1)  # type: ignore[index, arg-type]

    def test_movements_visible_to_accountant(self):
        self._post_note()
        self.client.logout()
        token = self._login("ketoan@test.com", "Ketoan123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.get("/api/stock/movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
