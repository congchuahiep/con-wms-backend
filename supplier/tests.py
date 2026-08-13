from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from iam.models import User


class SupplierAPITestCase(TestCase):
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

    def _login(self, email: str, password: str) -> str:
        response: Response = self.client.post(
            "/api/auth/login/", {"email": email, "password": password}
        )
        return response.data["access"]  # type: ignore[no-any-return]

    # ---------- GET list ----------

    def test_get_list_unauthenticated(self):
        response: Response = self.client.get("/api/suppliers/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_list_authenticated(self):
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.get("/api/suppliers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---------- POST ----------

    def test_create_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/suppliers/",
            {"code": "NCC_TEST", "name": "NCC Test", "taxCode": "9999999999"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "NCC_TEST")  # type: ignore[index]

    def test_create_storekeeper_forbidden(self):
        token: str = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.post(
            "/api/suppliers/",
            {"code": "NCC_TEST", "name": "NCC Test"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- PUT ----------

    def test_update_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/suppliers/",
            {"code": "NCC_TEST", "name": "NCC Test", "taxCode": "9999999999"},
        )
        supplier_id: Any = create_resp.data["id"]  # type: ignore[index]
        response: Response = self.client.put(
            f"/api/suppliers/{supplier_id}/",
            {"code": "NCC_TEST", "name": "NCC Test — updated", "taxCode": "9999999999"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "NCC Test — updated")  # type: ignore[index]

    def test_update_storekeeper_forbidden(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/suppliers/",
            {"code": "NCC_TEST", "name": "NCC Test", "taxCode": "9999999999"},
        )
        supplier_id: Any = create_resp.data["id"]  # type: ignore[index]
        self.client.logout()

        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.put(
            f"/api/suppliers/{supplier_id}/",
            {"code": "NCC_TEST", "name": "NCC Test — hacked", "taxCode": "9999999999"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------- DELETE (soft) ----------

    def test_delete_admin(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/suppliers/",
            {"code": "NCC_TEST", "name": "NCC Test", "taxCode": "9999999999"},
        )
        supplier_id: Any = create_resp.data["id"]  # type: ignore[index]
        response: Response = self.client.delete(f"/api/suppliers/{supplier_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete — still exists but is_active=False
        get_resp: Response = self.client.get(f"/api/suppliers/{supplier_id}/")
        self.assertEqual(get_resp.data["is_active"], False)  # type: ignore[index]

    def test_delete_storekeeper_forbidden(self):
        token: str = self._login("admin@test.com", "Admin123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create_resp: Response = self.client.post(
            "/api/suppliers/",
            {"code": "NCC_TEST", "name": "NCC Test", "taxCode": "9999999999"},
        )
        supplier_id: Any = create_resp.data["id"]  # type: ignore[index]
        self.client.logout()

        token = self._login("thukho@test.com", "Thukho123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response: Response = self.client.delete(f"/api/suppliers/{supplier_id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
