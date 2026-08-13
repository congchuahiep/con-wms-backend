# ty: ignore

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from iam.models import User

from .models import Material, MaterialCategory, Unit, UnitConversion


class MaterialCategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="admin123",
            role="admin",
        )
        self.storekeeper = User.objects.create_user(
            email="storekeeper@test.com",
            password="store123",
            role="storekeeper",
        )
        self.supervisor = User.objects.create_user(
            email="supervisor@test.com",
            password="super123",
            role="supervisor",
        )

        # Categories (tree: VLXD → XM, THEP → THEP_TRON; CAT leaf)
        self.vlxd = MaterialCategory.objects.create(
            code="VLXD", name="Vật liệu xây dựng", color="blue"
        )
        self.xm = MaterialCategory.objects.create(
            code="XM", name="Xi măng", parent=self.vlxd, color="red"
        )
        self.thep = MaterialCategory.objects.create(
            code="THEP", name="Thép", parent=self.vlxd, color="green"
        )
        self.thep_tron = MaterialCategory.objects.create(
            code="THEP_TRON", name="Thép tròn", parent=self.thep, color="orange"
        )
        self.cat = MaterialCategory.objects.create(
            code="CAT", name="Cát", parent=self.vlxd
        )

        self.list_url = reverse("category-list")
        self.detail_url = reverse("category-detail", kwargs={"pk": self.vlxd.pk})
        self.cat_detail_url = reverse("category-detail", kwargs={"pk": self.cat.pk})

    # ─── GET list — tree mode (default) ─────────────────────────

    def test_list_tree_requires_auth(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_tree_returns_only_root_nodes(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data
        # Chỉ có VLXD là root (parent=null)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "VLXD")

    def test_list_tree_has_nested_children(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url)
        root = resp.data[0]
        self.assertIn("children", root)
        children_codes = {c["code"] for c in root["children"]}
        self.assertEqual(children_codes, {"XM", "THEP", "CAT"})

    def test_list_tree_children_are_recursive(self):
        """THEP có con là THEP_TRON."""
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url)
        root = resp.data[0]
        thep = next(c for c in root["children"] if c["code"] == "THEP")
        self.assertEqual(len(thep["children"]), 1)
        self.assertEqual(thep["children"][0]["code"], "THEP_TRON")

    def test_list_tree_includes_color_field(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url)
        root = resp.data[0]
        self.assertEqual(root["color"], "blue")
        xm = next(c for c in root["children"] if c["code"] == "XM")
        self.assertEqual(xm["color"], "red")
        cat = next(c for c in root["children"] if c["code"] == "CAT")
        self.assertIsNone(cat["color"])

    # ─── GET list — flat mode ───────────────────────────────────

    def test_list_flat_returns_all_active(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url + "?flat=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 5)

    def test_list_flat_includes_depth_field(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url + "?flat=true")
        depths = {item["code"]: item["depth"] for item in resp.data}
        self.assertEqual(depths["VLXD"], 0)
        self.assertEqual(depths["XM"], 1)
        self.assertEqual(depths["THEP"], 1)
        self.assertEqual(depths["THEP_TRON"], 2)
        self.assertEqual(depths["CAT"], 1)

    def test_list_flat_parent_is_id(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url + "?flat=true")
        thep_tron = next(item for item in resp.data if item["code"] == "THEP_TRON")
        self.assertEqual(thep_tron["parent"], self.thep.pk)

    # ─── GET detail ─────────────────────────────────────────────

    def test_retrieve_category(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], "VLXD")
        self.assertEqual(resp.data["color"], "blue")

    # ─── POST create ────────────────────────────────────────────

    def test_create_category_admin(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            self.list_url,
            {"code": "DA", "name": "Đá", "color": "purple", "parentId": self.vlxd.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["code"], "DA")
        self.assertEqual(resp.data["color"], "purple")

    def test_create_category_storekeeper(self):
        self.client.force_authenticate(self.storekeeper)
        resp = self.client.post(
            self.list_url,
            {"code": "DA", "name": "Đá"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_category_forbidden(self):
        self.client.force_authenticate(self.supervisor)
        resp = self.client.post(
            self.list_url,
            {"code": "DA", "name": "Đá"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ─── PUT update ─────────────────────────────────────────────

    def test_update_category(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.put(
            self.detail_url,
            {"code": "VLXD", "name": "VLXD Updated", "color": "cyan"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "VLXD Updated")
        self.assertEqual(resp.data["color"], "cyan")

    # ─── DELETE hard delete ─────────────────────────────────────

    def test_delete_category(self):
        """Xóa cứng node lá (CAT) — trả về 200 + serializer data."""
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(self.cat_detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], self.cat.code)
        with self.assertRaises(MaterialCategory.DoesNotExist):
            MaterialCategory.objects.get(pk=self.cat.pk)

    def test_deleted_not_in_list(self):
        self.client.force_authenticate(self.admin)
        self.client.delete(self.cat_detail_url)
        resp = self.client.get(self.list_url)
        self.assertEqual(len(resp.data), 1)  # chỉ còn VLXD root

    def test_delete_category_blocked_by_material(self):
        """Xóa danh mục đang có Material liên kết → 409 Conflict."""
        Material.objects.create(
            code="DA-1X2", name="Đá 1x2", category=self.cat, unit=Unit.objects.create(code="M3", name="Mét khối")
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(self.cat_detail_url)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("detail", resp.data)
        self.assertIn("blocked_by", resp.data)
        self.assertIn("Vật tư — Đá 1x2", resp.data["blocked_by"][0])


class MaterialAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@test.com", password="admin123", role="admin"
        )
        self.storekeeper = User.objects.create_user(
            email="storekeeper@test.com", password="store123", role="storekeeper"
        )
        self.supervisor = User.objects.create_user(
            email="supervisor@test.com", password="super123", role="supervisor"
        )

        self.category = MaterialCategory.objects.create(code="XM", name="Xi măng")
        self.unit = Unit.objects.create(code="BAO", name="Bao")

        self.material = Material.objects.create(
            code="XM-HT-PCB40",
            name="Xi măng Hà Tiên PCB40",
            category=self.category,
            unit=self.unit,
            description="PCB40, 50kg/bao",
        )

        self.list_url = reverse("material-list")
        self.detail_url = reverse("material-detail", kwargs={"pk": self.material.pk})

    # ─── GET list ───────────────────────────────────────────────

    def test_list_requires_auth(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_paginated(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("items", resp.data)
        self.assertEqual(len(resp.data["items"]), 1)
        self.assertEqual(resp.data["items"][0]["code"], "XM-HT-PCB40")

    def test_list_filter_by_category(self):
        MaterialCategory.objects.create(code="CAT", name="Cát")
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url + "?category=" + str(self.category.pk))
        self.assertEqual(len(resp.data["items"]), 1)
        resp2 = self.client.get(self.list_url + "?category=999")
        self.assertEqual(len(resp2.data["items"]), 0)

    def test_list_search(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url + "?search=Hà Tiên")
        self.assertEqual(len(resp.data["items"]), 1)
        resp2 = self.client.get(self.list_url + "?search=KHÔNG_TỒN_TẠI")
        self.assertEqual(len(resp2.data["items"]), 0)

    # ─── GET detail ─────────────────────────────────────────────

    def test_retrieve_material(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], "XM-HT-PCB40")
        self.assertIn("category", resp.data)
        self.assertEqual(resp.data["category"]["code"], "XM")

    # ─── POST create ────────────────────────────────────────────

    def test_create_material_admin(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            self.list_url,
            {
                "code": "XM-BS-PCB30",
                "name": "Xi măng Bỉm Sơn PCB30",
                "categoryId": self.category.pk,
                "unitId": self.unit.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_material_storekeeper(self):
        self.client.force_authenticate(self.storekeeper)
        resp = self.client.post(
            self.list_url,
            {
                "code": "XM-BS-PCB30",
                "name": "Xi măng Bỉm Sơn PCB30",
                "categoryId": self.category.pk,
                "unitId": self.unit.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_material_forbidden(self):
        self.client.force_authenticate(self.supervisor)
        resp = self.client.post(
            self.list_url,
            {
                "code": "XM-BS-PCB30",
                "name": "Xi măng Bỉm Sơn PCB30",
                "categoryId": self.category.pk,
                "unitId": self.unit.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ─── PUT update ─────────────────────────────────────────────

    def test_update_material(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.put(
            self.detail_url,
            {
                "code": "XM-HT-PCB40",
                "name": "Xi măng Hà Tiên PCB40 (updated)",
                "categoryId": self.category.pk,
                "unitId": self.unit.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Xi măng Hà Tiên PCB40 (updated)")

    # ─── DELETE hard delete ─────────────────────────────────────

    def test_delete_material(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], self.material.code)
        with self.assertRaises(Material.DoesNotExist):
            Material.objects.get(pk=self.material.pk)


class UnitAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@test.com", password="admin123", role="admin"
        )
        self.supervisor = User.objects.create_user(
            email="supervisor@test.com", password="super123", role="supervisor"
        )

        self.unit = Unit.objects.create(code="BAO", name="Bao")
        Unit.objects.create(code="KG", name="Kilogram")

        self.list_url = reverse("unit-list")
        self.detail_url = reverse("unit-detail", kwargs={"pk": self.unit.pk})

    def test_list_requires_auth(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_all(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_create_unit(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            self.list_url, {"code": "TAN", "name": "Tấn"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_unit_forbidden(self):
        self.client.force_authenticate(self.supervisor)
        resp = self.client.post(
            self.list_url, {"code": "TAN", "name": "Tấn"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_unit(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["code"], self.unit.code)
        with self.assertRaises(Unit.DoesNotExist):
            Unit.objects.get(pk=self.unit.pk)

    def test_delete_unit_blocked_by_material(self):
        """Xóa Unit đang được Material liên kết → 409 Conflict."""
        Material.objects.create(
            code="XM-TEST", name="Test",
            category=MaterialCategory.objects.create(code="TEST", name="Test"),
            unit=self.unit,
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("blocked_by", resp.data)


class UnitConversionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@test.com", password="admin123", role="admin"
        )

        self.unit_bao = Unit.objects.create(
            code="BAO", name="Bao", conversion_type="material"
        )
        self.unit_kg = Unit.objects.create(
            code="KG", name="Kilogram", conversion_type="global"
        )
        self.unit_tan = Unit.objects.create(
            code="TAN", name="Tấn", conversion_type="global"
        )

        self.category = MaterialCategory.objects.create(code="XM", name="Xi măng")
        self.material = Material.objects.create(
            code="XM-HT-PCB40",
            name="Xi măng Hà Tiên PCB40",
            category=self.category,
            unit=self.unit_bao,
        )

        # Material-specific conversion: BAO → KG cho XM Hà Tiên
        self.mat_conv = UnitConversion.objects.create(
            from_unit=self.unit_bao,
            to_unit=self.unit_kg,
            factor=50,
            material=self.material,
        )
        # Global conversion: TAN → KG
        self.global_conv = UnitConversion.objects.create(
            from_unit=self.unit_tan,
            to_unit=self.unit_kg,
            factor=1000,
        )

        self.bao_url = reverse(
            "unit-detail", kwargs={"pk": self.unit_bao.pk}
        )
        self.kg_url = reverse(
            "unit-detail", kwargs={"pk": self.unit_kg.pk}
        )
        self.tan_url = reverse(
            "unit-detail", kwargs={"pk": self.unit_tan.pk}
        )
        self.create_bao_url = reverse(
            "unit-create-conversion", kwargs={"pk": self.unit_bao.pk}
        )
        self.create_tan_url = reverse(
            "unit-create-conversion", kwargs={"pk": self.unit_tan.pk}
        )

    def test_detail_conversions_material(self):
        """GET /units/BAO/ — material, chỉ có direct."""
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.bao_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["conversion_type"], "material")
        self.assertEqual(len(resp.data["conversions"]), 1)
        conv = resp.data["conversions"][0]
        self.assertEqual(conv["id"], self.mat_conv.pk)
        self.assertFalse(conv["is_reverse"])
        self.assertIsNotNone(conv["material"])

    def test_detail_conversions_global_direct(self):
        """GET /units/TAN/ — global, có direct TAN → KG."""
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.tan_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["conversion_type"], "global")
        self.assertTrue(any(
            not c["is_reverse"] and c["id"] == self.global_conv.pk
            for c in resp.data["conversions"]
        ))

    def test_detail_conversions_global_reverse(self):
        """GET /units/KG/ — global, thấy reverse từ TAN → KG."""
        self.client.force_authenticate(self.admin)
        resp = self.client.get(self.kg_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        reverse_item = next(
            (c for c in resp.data["conversions"] if c["is_reverse"]),
            None
        )
        self.assertIsNotNone(reverse_item)
        self.assertEqual(reverse_item["id"], self.global_conv.pk)
        self.assertEqual(reverse_item["to_unit"]["code"], "TAN")

    def test_create_conversion_material(self):
        """POST /units/BAO/conversions/ — material, có materialId → 201."""
        self.client.force_authenticate(self.admin)
        mat2 = Material.objects.create(
            code="XM-BS-PCB30",
            name="Xi măng Bỉm Sơn PCB30",
            category=self.category,
            unit=self.unit_bao,
        )
        resp = self.client.post(
            self.create_bao_url,
            {"toUnitId": self.unit_kg.pk, "factor": 40, "materialId": mat2.pk},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(resp.data["material"])
        self.assertFalse(resp.data["is_reverse"])

    def test_create_conversion_material_missing_material(self):
        """POST /units/BAO/conversions/ — material, thiếu materialId → 400."""
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            self.create_bao_url,
            {"toUnitId": self.unit_kg.pk, "factor": 40},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("material_id", resp.data)

    def test_create_conversion_global(self):
        """POST /units/TAN/conversions/ — global, không materialId → 201."""
        self.client.force_authenticate(self.admin)
        gram = Unit.objects.create(
            code="G", name="Gram", conversion_type="global"
        )
        resp = self.client.post(
            self.create_tan_url,
            {"toUnitId": gram.pk, "factor": 1000000},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(resp.data["material"])
        self.assertFalse(resp.data["is_reverse"])

    def test_create_conversion_global_with_material(self):
        """POST /units/TAN/conversions/ — global, gửi kèm materialId → 400."""
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            self.create_tan_url,
            {
                "toUnitId": self.unit_kg.pk,
                "factor": 500,
                "materialId": self.material.pk,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("material_id", resp.data)

    def test_update_conversion(self):
        self.client.force_authenticate(self.admin)
        url = reverse(
            "unit-conversion-detail", kwargs={"pk": self.mat_conv.pk}
        )
        resp = self.client.patch(url, {"factor": 55}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.mat_conv.refresh_from_db()
        self.assertEqual(self.mat_conv.factor, 55)

    def test_delete_conversion(self):
        self.client.force_authenticate(self.admin)
        url = reverse(
            "unit-conversion-detail", kwargs={"pk": self.mat_conv.pk}
        )
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        with self.assertRaises(UnitConversion.DoesNotExist):
            UnitConversion.objects.get(pk=self.mat_conv.pk)
