from decimal import Decimal
from uuid import uuid4

from django.db.models import Sum
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.test import APIClient

from catalog.models import Material, MaterialCategory, Unit
from iam.models import User
from inventory.models import InboundNote, InboundNoteLine, OutboundNote, StockMovement
from supplier.models import Supplier
from warehouse.models import Warehouse

from .models import Site, SiteMaterialRequirement


class SiteWarehouseAutoCreateTestCase(TestCase):
    """Kho công trường tự động tạo khi tạo Site (signal post_save)."""

    def test_create_site_auto_creates_warehouse(self):
        site = Site.objects.create(code="CT_RG", name="Công trường cầu Rạch Giá")

        warehouse = Warehouse.objects.get(site=site)
        self.assertEqual(warehouse.code, "KHO_CT_RG")
        self.assertIn("Công trường cầu Rạch Giá", warehouse.name)
        self.assertIsNone(warehouse.latitude)

    def test_update_site_does_not_create_second_warehouse(self):
        site = Site.objects.create(code="CT_RG", name="CT A")
        site.name = "Công trường cầu Rạch Giá — đổi tên"
        site.save()

        self.assertEqual(Warehouse.objects.filter(site=site).count(), 1)

    def test_long_site_code_truncated_to_20_chars(self):
        code = "CT_" + "X" * 18  # 21 ký tự
        Site.objects.create(code=code, name="CT dài")

        warehouse = Warehouse.objects.get(code__startswith="KHO_")
        self.assertLessEqual(len(warehouse.code), 20)
        self.assertTrue(warehouse.code.startswith("KHO_"))

    def test_soft_delete_site_keeps_warehouse(self):
        site = Site.objects.create(code="CT_RG", name="CT")
        site.status = Site.Status.INACTIVE
        site.save()

        self.assertTrue(Warehouse.objects.filter(site=site, is_active=True).exists())

    def test_central_warehouse_has_no_site(self):
        central = Warehouse.objects.create(code="KHO_CHINH", name="Kho chính")
        self.assertIsNone(central.site)

    def test_site_has_exactly_one_warehouse(self):
        Site.objects.create(code="CT_RG", name="CT Rạch Giá")
        site = Site.objects.get(code="CT_RG")
        self.assertIsNotNone(site.warehouse)
        self.assertEqual(Warehouse.objects.filter(site=site).count(), 1)

    def test_new_site_status_active(self):
        site = Site.objects.create(code="CT_MOI", name="CT mới")
        self.assertEqual(site.status, Site.Status.ACTIVE)


class SiteRequirementSettleTestCase(TestCase):
    """Định mức vật tư công trường + tất toán."""

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
        )

        self.site = Site.objects.create(code="CT_SO", name="Công trường Sông Ông")
        self.site_warehouse = self.site.warehouse
        self.target = Warehouse.objects.create(code="KHO_CHINH", name="Kho chính")
        self.supplier = Supplier.objects.create(
            code="NCC_TEST", name="NCC test", tax_code="9999999999"
        )
        self.category = MaterialCategory.objects.create(
            code="CAT_TEST", name="Danh mục test"
        )
        unit_bao = Unit.objects.create(code="BAO", name="Bao")
        unit_vien = Unit.objects.create(code="VIEN", name="Viên")
        unit_cai = Unit.objects.create(code="CAI", name="Cái")
        self.cement = Material.objects.create(
            code="XM", name="Xi măng PCB40", category=self.category, unit=unit_bao
        )
        self.brick = Material.objects.create(
            code="GACH", name="Gạch ống", category=self.category, unit=unit_vien
        )
        self.drill = Material.objects.create(
            code="MAYKHOAN", name="Máy khoan", category=self.category, unit=unit_cai
        )

    # ---------- helpers ----------

    def _login(self, email: str, password: str) -> str:
        response: Response = self.client.post(
            "/api/auth/login/", {"email": email, "password": password}
        )
        return response.data["access"]

    def _login_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self._login('admin@test.com', 'Admin123!')}"
        )

    def _add_stock(self, material: Material, quantity: str):
        """Ghi sổ kho trực tiếp qua 1 phiếu nhập mua đã chốt."""
        note = InboundNote.objects.create(
            number=f"PN-TEST-{uuid4().hex[:8]}",
            note_type=InboundNote.Type.PURCHASE,
            date="2026-09-20",
            warehouse=self.site_warehouse,
            supplier=self.supplier,
            note="Test",
            created_by=self.admin,
        )
        InboundNoteLine.objects.create(
            inbound_note=note,
            material=material,
            quantity=Decimal(quantity),
            unit_price=Decimal(1000),
        )
        note.post(self.admin)

    def _put_requirements(self, lines):
        self._login_admin()
        return self.client.put(
            f"/api/sites/{self.site.id}/requirements/",
            {"lines": lines},
            format="json",
        )

    def _stock_balance(self, warehouse: Warehouse, material: Material) -> Decimal:
        total = StockMovement.objects.filter(
            warehouse=warehouse, material=material
        ).aggregate(total=Sum("quantity"))["total"]
        return total or Decimal(0)

    # ---------- GET / PUT requirements ----------

    def test_get_requirements_compares_plan_with_stock(self):
        self._add_stock(self.cement, "5")
        self._add_stock(self.drill, "1")
        self._put_requirements(
            [
                {"materialId": self.cement.id, "quantity": "3"},
                {"materialId": self.brick.id, "quantity": "20000"},
            ]
        )

        self._login_admin()
        response = self.client.get(f"/api/sites/{self.site.id}/requirements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = {row["material"]["code"]: row for row in response.data}

        self.assertEqual(rows["XM"]["required_quantity"], "3.000")
        self.assertEqual(rows["XM"]["balance"], "5.000")
        self.assertEqual(rows["XM"]["status"], "sufficient")
        self.assertEqual(rows["XM"]["default_return_quantity"], "2.000")

        self.assertEqual(rows["GACH"]["required_quantity"], "20000.000")
        self.assertEqual(rows["GACH"]["balance"], "0.000")
        self.assertEqual(rows["GACH"]["status"], "insufficient")
        self.assertEqual(rows["GACH"]["default_return_quantity"], "0.000")

        self.assertIsNone(rows["MAYKHOAN"]["required_quantity"])
        self.assertEqual(rows["MAYKHOAN"]["balance"], "1.000")
        self.assertEqual(rows["MAYKHOAN"]["status"], "not_in_plan")
        self.assertEqual(rows["MAYKHOAN"]["default_return_quantity"], "1.000")

    def test_put_requirements_replaces_all_lines(self):
        self._put_requirements([{"materialId": self.cement.id, "quantity": "3"}])
        self._put_requirements([{"materialId": self.brick.id, "quantity": "20000"}])

        reqs = SiteMaterialRequirement.objects.filter(site=self.site)
        self.assertEqual(reqs.count(), 1)
        self.assertEqual(reqs.first().material, self.brick)

    def test_put_requirements_empty_clears(self):
        self._put_requirements([{"materialId": self.cement.id, "quantity": "3"}])
        response = self._put_requirements([])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SiteMaterialRequirement.objects.filter(site=self.site).count(), 0)

    def test_put_requirements_quantity_must_be_positive(self):
        response = self._put_requirements(
            [{"materialId": self.cement.id, "quantity": "0"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_requirements_duplicate_material_rejected(self):
        response = self._put_requirements(
            [
                {"materialId": self.cement.id, "quantity": "3"},
                {"materialId": self.cement.id, "quantity": "4"},
            ]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_requirements_rejected_when_site_closed(self):
        self._put_requirements([{"materialId": self.cement.id, "quantity": "3"}])
        self.site.status = Site.Status.COMPLETED
        self.site.save()
        response = self._put_requirements(
            [{"materialId": self.cement.id, "quantity": "5"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requirements_readable_by_any_authenticated_user(self):
        self._put_requirements([{"materialId": self.cement.id, "quantity": "3"}])
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self._login('thukho@test.com', 'Thukho123!')}"
        )
        response = self.client.get(f"/api/sites/{self.site.id}/requirements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---------- settle ----------

    def _settle(self, to_warehouse_id: int, lines):
        self._login_admin()
        return self.client.post(
            f"/api/sites/{self.site.id}/settle/",
            {"toWarehouseId": to_warehouse_id, "lines": lines},
            format="json",
        )

    def _default_setup(self):
        """Công trường đủ định mức: XM 5 (cần 3), GACH 25000 (cần 20000), máy khoan 1."""
        self._put_requirements(
            [
                {"materialId": self.cement.id, "quantity": "3"},
                {"materialId": self.brick.id, "quantity": "20000"},
            ]
        )
        self._add_stock(self.cement, "5")
        self._add_stock(self.brick, "25000")
        self._add_stock(self.drill, "1")

    def _assert_closed(self, site: Site):
        self.site.refresh_from_db()
        self.assertEqual(self.site.status, Site.Status.COMPLETED)
        self.assertIsNotNone(self.site.settled_at)
        self.assertEqual(self.site.settled_by, self.admin)
        self.site_warehouse.refresh_from_db()
        self.assertFalse(self.site_warehouse.is_active)

    def test_settle_success_moves_excess_and_extra(self):
        self._default_setup()
        response = self._settle(
            self.target.id,
            [
                {"materialId": self.cement.id, "quantity": "2"},
                {"materialId": self.brick.id, "quantity": "5000"},
                {"materialId": self.drill.id, "quantity": "1"},
            ],
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self._assert_closed(self.site)

        note = OutboundNote.objects.get(number=response.data["outbound_note"]["number"])
        self.assertEqual(note.note_type, OutboundNote.Type.TRANSFER)
        self.assertEqual(note.status, OutboundNote.Status.POSTED)
        self.assertEqual(note.warehouse, self.site_warehouse)
        self.assertEqual(note.to_warehouse, self.target)
        self.assertEqual(note.lines.count(), 3)

        # Sổ kho: kho CT giữ phần định mức, kho đích nhận phần trả về
        self.assertEqual(
            self._stock_balance(self.site_warehouse, self.cement), Decimal(3)
        )
        self.assertEqual(
            self._stock_balance(self.site_warehouse, self.brick), Decimal(20000)
        )
        self.assertEqual(
            self._stock_balance(self.site_warehouse, self.drill), Decimal(0)
        )
        self.assertEqual(self._stock_balance(self.target, self.cement), Decimal(2))
        self.assertEqual(self._stock_balance(self.target, self.brick), Decimal(5000))
        self.assertEqual(self._stock_balance(self.target, self.drill), Decimal(1))

    def test_settle_blocked_when_requirement_not_met(self):
        self._put_requirements(
            [{"materialId": self.brick.id, "quantity": "20000"}]
        )
        self._add_stock(self.brick, "10000")  # thiếu
        response = self._settle(
            self.target.id, [{"materialId": self.brick.id, "quantity": "10000"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("GACH", str(response.data["fields"]["lines"]))

    def test_settle_blocked_when_quantity_exceeds_balance(self):
        self._default_setup()
        response = self._settle(
            self.target.id, [{"materialId": self.drill.id, "quantity": "2"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_settle_blocked_when_target_warehouse_inactive(self):
        self._default_setup()
        self.target.is_active = False
        self.target.save()
        response = self._settle(
            self.target.id, [{"materialId": self.drill.id, "quantity": "1"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_settle_requires_reason_when_below_default(self):
        self._default_setup()
        # XM mặc định trả 2 (tồn 5 − định mức 3) — trả 1 phải ghi lý do
        response = self._settle(
            self.target.id, [{"materialId": self.cement.id, "quantity": "1"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lý do", str(response.data["fields"]["lines"]))

        response = self._settle(
            self.target.id,
            [{"materialId": self.cement.id, "quantity": "1", "note": "Xi bị ẩm, giữ lại"}],
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        note = OutboundNote.objects.get(number=response.data["outbound_note"]["number"])
        line = note.lines.get(material=self.cement)
        self.assertEqual(line.note, "Xi bị ẩm, giữ lại")

    def test_settle_blocked_when_already_completed(self):
        self._default_setup()
        self._settle(
            self.target.id,
            [
                {"materialId": self.cement.id, "quantity": "2"},
                {"materialId": self.brick.id, "quantity": "5000"},
                {"materialId": self.drill.id, "quantity": "1"},
            ],
        )
        response = self._settle(
            self.target.id, [{"materialId": self.drill.id, "quantity": "1"}]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_notes_blocked_after_settlement(self):
        self._default_setup()
        self._settle(
            self.target.id,
            [
                {"materialId": self.cement.id, "quantity": "2"},
                {"materialId": self.brick.id, "quantity": "5000"},
                {"materialId": self.drill.id, "quantity": "1"},
            ],
        )

        # 1. Tạo phiếu nhập mới vào kho đã đóng → 400 (serializer guard)
        self._login_admin()
        response = self.client.post(
            "/api/inbound-notes/",
            {
                "note_type": "purchase",
                "date": "2026-09-21",
                "warehouse_id": self.site_warehouse.id,
                "supplier_id": self.supplier.id,
                "lines": [{"material_id": self.cement.id, "quantity": "1", "unit_price": "1000"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # serializer guard

        # 2. Nháp tạo TRƯỚC khi đóng, chốt SAU khi đóng → 400 (BaseNote.post guard)
        self.site_warehouse.refresh_from_db()
        draft = InboundNote.objects.create(
            number=f"PN-TEST-{uuid4().hex[:8]}",
            note_type=InboundNote.Type.PURCHASE,
            date="2026-09-20",
            warehouse=self.site_warehouse,
            supplier=self.supplier,
            note="Nháp cũ",
            created_by=self.admin,
        )
        InboundNoteLine.objects.create(
            inbound_note=draft,
            material=self.cement,
            quantity=Decimal(1),
            unit_price=Decimal(1000),
        )
        with self.assertRaises(DRFValidationError):
            draft.post(self.admin)
        self.assertEqual(draft.status, InboundNote.Status.DRAFT)

        # 3. Điều chuyển vào kho đã đóng → 400
        response = self.client.post(
            "/api/outbound-notes/",
            {
                "note_type": "transfer",
                "date": "2026-09-21",
                "warehouse_id": self.target.id,
                "to_warehouse_id": self.site_warehouse.id,
                "lines": [{"material_id": self.cement.id, "quantity": "1"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- list filter + destroy ----------

    def test_list_defaults_active_only(self):
        Site.objects.create(code="CT_DONE", name="CT đã xong", status=Site.Status.COMPLETED)
        self._login_admin()
        response = self.client.get("/api/sites/")
        codes = [row["code"] for row in response.data]
        self.assertIn("CT_SO", codes)
        self.assertNotIn("CT_DONE", codes)

        response = self.client.get("/api/sites/?status=all")
        codes = [row["code"] for row in response.data]
        self.assertIn("CT_DONE", codes)

    def test_destroy_sets_status_inactive(self):
        self._login_admin()
        response = self.client.delete(f"/api/sites/{self.site.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.site.refresh_from_db()
        self.assertEqual(self.site.status, Site.Status.INACTIVE)