from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Chỉ admin mới được truy cập."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsStorekeeper(BasePermission):
    """Chỉ thủ kho."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "storekeeper"


class IsAdminOrStorekeeper(BasePermission):
    """Admin hoặc thủ kho."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "admin",
            "storekeeper",
        )


class IsAdminOrAccountant(BasePermission):
    """
    Admin hoặc kế toán.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "admin",
            "accountant",
        )


class IsAdminOrSupervisor(BasePermission):
    """Admin hoặc chủ nhiệm công trình."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "admin",
            "supervisor",
        )
