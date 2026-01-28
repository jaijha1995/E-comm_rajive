from rest_framework.permissions import BasePermission
from superadmin.models import UserProfile

class IsAuthenticatedAndActive(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        if not user:
            return False

        # ✅ WebSocket case: UserProfile
        if isinstance(user, UserProfile):
            return bool(
                getattr(user, "role", None) and
                getattr(user, "is_active", True)
            )

        # ✅ REST API case: auth.User
        if hasattr(user, "is_authenticated"):
            return (
                user.is_authenticated and
                getattr(user, "is_active", True) and
                hasattr(user, "role")
            )

        return False


# ================= ROLE BASED =================

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            IsAuthenticatedAndActive().has_permission(request, view)
            and request.user.role == "superadmin"
        )



class Iscustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            IsAuthenticatedAndActive().has_permission(request, view)
            and request.user.role == "customer"
        )


# ================= Category Created  =================

class CanCreateCategory(BasePermission):
    def has_permission(self, request, view):
        return (
            IsAuthenticatedAndActive().has_permission(request, view)
            and request.user.role in (
                "superadmin"
            )
        )