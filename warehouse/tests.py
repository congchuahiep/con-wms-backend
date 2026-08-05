from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from iam.models import User


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
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "KHO_TEST")  # type: ignore[index]

    def test_create_storekeeper_forbidden(self):
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- PUT ----------

    def test_update_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        response: Response = self.client.put(
            f"/api/warehouses/{warehouse_id}/",
            {"code": "KHO_TEST", "name": "Kho test — updated"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Kho test — updated")  # type: ignore[index]

    def test_update_storekeeper_forbidden(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        self.client.logout()

        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.put(
            f"/api/warehouses/{warehouse_id}/",
            {"code": "KHO_TEST", "name": "Kho test — hacked"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- DELETE (soft) ----------

    def test_delete_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/warehouses/",
            {"code": "KHO_TEST", "name": "Kho test"},
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
        )
        warehouse_id: Any = create_resp.data["id"]  # type: ignore[index]
        self.client.logout()

        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.delete(f"/api/warehouses/{warehouse_id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
