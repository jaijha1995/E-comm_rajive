# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from .Usa_state import USA_STATES

# Roles
ROLE_SUPERADMIN = "superadmin"
ROLE_CUSTOMER = "customer"
ROLE_LABORATORY = "Laboratory(manually reviewed)"

ROLE_CHOICES = [
    (ROLE_SUPERADMIN, "superadmin"),
    (ROLE_CUSTOMER, "customer"),
]

ROLE_TYPE = [
    (ROLE_LABORATORY, "Laboratory(manually reviewed)"),
]


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")

        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", ROLE_SUPERADMIN)
        return self.create_user(email, password, **extra_fields)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True,db_index=True)
    user_type = models.CharField(max_length=255, blank=True, db_index=True , choices=ROLE_TYPE)
    first_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    last_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    Company_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, db_index=True)
    Street_Address = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    Address_Line_2 = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    Country_and_State = models.CharField(max_length=255, blank=True, null=True, db_index=True , choices=USA_STATES)
    Town_City = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    Zip_Code = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def clean(self):
        allowed_roles = {r[0] for r in ROLE_CHOICES}
        if self.role not in allowed_roles:
            raise ValidationError({'role': 'Invalid role value.'})

    @staticmethod
    def can_create_role(creator_role, target_role):
        if creator_role == ROLE_SUPERADMIN:
            return target_role == ROLE_CUSTOMER
        return False

    @property
    def is_superadmin(self):
        return self.role == ROLE_SUPERADMIN

    @property
    def is_customer(self):
        return self.role == ROLE_CUSTOMER

    def __str__(self):
        return self.email