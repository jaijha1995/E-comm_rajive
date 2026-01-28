from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.utils.crypto import get_random_string
from .models import (
    UserProfile,
    ROLE_SUPERADMIN,
    ROLE_CUSTOMER,
)
from .tasks import send_welcome_email
from .serializers import UserSerializer, UserListSerializer
from .utils import send_otp, verify_otp


class CustomerViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()

        # --- Normalize input ---
        if "email" in data and data["email"]:
            data["email"] = data["email"].lower().strip()

        # --- Bootstrap: create the first SuperAdmin (no auth required) ---
        if not UserProfile.objects.exists():
            serializer = UserSerializer(data=data, context={"request": request})
            if not serializer.is_valid():
                return Response({"status": "failure", "errors": serializer.errors}, status=400)

            generated_password = get_random_string(12)
            with transaction.atomic():
                user = serializer.save(role=ROLE_SUPERADMIN, is_active=True)
                user.set_password(generated_password)
                user.save()

            try:
                send_welcome_email.delay(
                    user.email,
                    {
                        "subject": "Welcome SuperAdmin",
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "password": generated_password,
                        "msg": "Your account has been created with a temporary password."
                    },
                )
            except Exception:
                pass

            return Response(
                {"status": "success", "msg": "SuperAdmin created. Password sent to email.", "data": UserSerializer(user).data},
                status=201,
            )

        # --- Subsequent creations (Public Signup for Customers) ---
        serializer = UserSerializer(data=data, context={"request": request})
        if not serializer.is_valid():
            return Response({"status": "failure", "errors": serializer.errors}, status=400)

        generated_password = get_random_string(12)
        with transaction.atomic():
            user = serializer.save(role=ROLE_CUSTOMER, is_active=False)
            user.set_password(generated_password)
            user.save()

        try:
            send_welcome_email.delay(
                user.email,
                {
                    "subject": "Welcome to E-comm",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "password": generated_password,
                    "msg": "Your registration is successful. Please wait for admin approval."
                },
            )
        except Exception:
            pass

        return Response(
            {"status": "success", "msg": "Registration successful. Please check your email for the password. Account activation is pending admin review.", "data": UserSerializer(user).data},
            status=201,
        )


# -------------------------
# Login
# -------------------------
class LoginCustomer(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"msg": "Email and password required"}, status=400)

        try:
            user = UserProfile.objects.get(email=email.lower())
        except UserProfile.DoesNotExist:
            return Response({"msg": "Invalid email"}, status=404)

        # check if active
        if not user.is_active:
            return Response({"msg": "You are not active user, please connect with admin"}, status=403)

        if not user.check_password(password):
            return Response({"msg": "Invalid password"}, status=401)

        refresh = RefreshToken.for_user(user)

        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
        }

        return Response(
            {
                "status": "success",
                "msg": f"{user.role} login successful",
                "data": data,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            },
            status=200,
        )

class CustomerManageViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        current_user = request.user

        if id:
            user = get_object_or_404(UserProfile, id=id)
            return Response({"data": UserSerializer(user).data}, status=200)

        # superadmins see all users
        if getattr(current_user, "is_superadmin", False):
            users = UserProfile.objects.all().select_related("parent", "root_company")
        else:
            # non-superadmins: show users in the same company chain or direct children
            users = UserProfile.objects.select_related("parent", "root_company").filter(
                Q(root_company=current_user.root_company) | Q(parent=current_user)
            )

        return Response({"data": UserListSerializer(users, many=True).data}, status=200)

    def patch(self, request, id=None):
        if not id:
            return Response({"msg": "User ID required"}, status=400)

        user = get_object_or_404(UserProfile, id=id)
        current_user = request.user

        # Only SuperAdmin or the parent (creator) can edit
        if not (getattr(current_user, "is_superadmin", False) or user.parent == current_user):
            return Response({"msg": "You are not authorized to edit this user"}, status=403)

        serializer = UserSerializer(user, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)

        serializer.save()
        return Response({"data": serializer.data}, status=200)

    def delete(self, request, id=None):
        if not id:
            return Response({"msg": "User ID required"}, status=400)

        user = get_object_or_404(UserProfile, id=id)
        current_user = request.user

        allowed = False
        if getattr(current_user, "is_superadmin", False):
            allowed = True
        if user.parent == current_user:
            allowed = True

        if not allowed:
            return Response({"msg": "You are not authorized to delete this user"}, status=403)

        user.delete()
        return Response({"msg": "User deleted successfully"}, status=200)


# -------------------------
# OTP endpoints
# -------------------------
class OTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)
        ok, msg = send_otp(email)
        if not ok:
            return Response({"error": msg}, status=429)
        return Response({"message": msg}, status=200)


class VerifyOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not email or not otp:
            return Response({"error": "Email and OTP required"}, status=400)
        ok, msg = verify_otp(email, otp)
        if not ok:
            return Response({"error": msg}, status=400)
        return Response({"message": msg}, status=200)


# -------------------------
# Forgot password (via OTP)
# -------------------------
class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        otp = request.data.get("otp")

        if not all([email, password, confirm_password, otp]):
            return Response(
                {"error": "All fields are required: email, password, confirm_password, otp"}, status=400
            )

        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        ok, msg = verify_otp(email, otp)
        if not ok:
            return Response({"error": msg}, status=400)

        try:
            user = UserProfile.objects.get(email=email.lower())
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.password = make_password(password)
        user.save(update_fields=["password"])
        return Response({"message": "Password reset successful"}, status=200)
