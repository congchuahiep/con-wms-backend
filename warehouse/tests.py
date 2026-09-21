from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from iam.models import User
from sites.models import Site
from warehouse.models import Warehouse


class WarehouseAPITestCase(TestCase):
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
        self.supervisor = User.objects.create_user(
            email="chunhiem@test.com",
            password="Chunhiem123!",
            role="supervisor",
            first_name="Chu",
            last_name="Nhiem",
        )

    def _login(self, email: str, password: str) -> str:
        response: Response = self.client.post(
            "/api/auth/login/", {"email": email, "password": password}
        )
        return response.data["access"]  # type: ignore[no-any-return]

    # ---------- GET list ----------

    def test_get_list_unauthenticated(self):
        response: Response = self.client.get("/api/warehouses/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_list_authenticated(self):
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.get("/api/warehouses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---------- POST ----------

    def test_create_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "KHO_TEST")  # type: ignore[index]

    def test_create_storekeeper_forbidden(self):
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- PUT ----------

    def test_update_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
            format="json",
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        response: Response = self.client.put(
            f"/api/warehouses/{warehouse_id}/",
            {"code": "KHO_TEST", "name": "Kho test — updated"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Kho test — updated")  # type: ignore[index]

    def test_update_storekeeper_forbidden(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
            format="json",
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        self.client.logout()

        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.put(
            f"/api/warehouses/{warehouse_id}/",
            {"code": "KHO_TEST", "name": "Kho test — hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- DELETE (soft) ----------

    def test_delete_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
            format="json",
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        response: Response = self.client.delete(f"/api/warehouses/{warehouse_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete — still exists but is_active=False
        get_resp: Response = self.client.get(f"/api/warehouses/{warehouse_id}/")
        self.assertEqual(get_resp.data["is_active"], False)  # type: ignore[index]

    def test_delete_storekeeper_forbidden(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
            format="json",
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        self.client.logout()

        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.delete(f"/api/warehouses/{warehouse_id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- Site warehouse (kho công trường) ----------

    def test_list_default_excludes_site_warehouses(self):
        Site.objects.create(code="CT_RG", name="Công trường cầu Rạch Giá")
        Warehouse.objects.create(code="KHO_CHINH", name="Kho chính")
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response: Response = self.client.get("/api/warehouses/")
        codes = [r["code"] for r in response.data]  # type: ignore[index]
        self.assertIn("KHO_CHINH", codes)
        self.assertNotIn("KHO_CT_RG", codes)

    def test_list_include_site_param_returns_site_warehouses(self):
        Site.objects.create(code="CT_RG", name="Công trường cầu Rạch Giá")
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response: Response = self.client.get("/api/warehouses/?include_site=true")
        row = next(r for r in response.data if r["code"] == "KHO_CT_RG")  # type: ignore[index]
        self.assertEqual(row["site"]["code"], "CT_RG")  # type: ignore[index, union-attr]

    def test_list_site_null_for_central_warehouse(self):
        Warehouse.objects.create(code="KHO_CHINH", name="Kho chính")
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response: Response = self.client.get("/api/warehouses/")
        row = next(r for r in response.data if r["code"] == "KHO_CHINH")  # type: ignore[index]
        self.assertIsNone(row["site"])  # type: ignore[index]

    def test_delete_site_warehouse_forbidden(self):
        site = Site.objects.create(code="CT_RG", name="CT Rạch Giá")
        warehouse = Warehouse.objects.get(site=site)
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Scope mặc định: kho công trường không nằm trong danh sách (404)
        default_resp: Response = self.client.delete(f"/api/warehouses/{warehouse.id}/")
        self.assertEqual(default_resp.status_code, status.HTTP_404_NOT_FOUND)

        # Kể cả khi lấy đủ (include_site) cũng bị chặn xóa (guard 400)
        guard_resp: Response = self.client.delete(
            f"/api/warehouses/{warehouse.id}/?include_site=true"
        )
        self.assertEqual(guard_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            Warehouse.objects.filter(id=warehouse.id, is_active=True).exists()
        )
