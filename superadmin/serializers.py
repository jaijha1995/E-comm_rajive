from rest_framework import serializers
from django.core.validators import validate_email
from django.db import transaction
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile._meta.get_field('role').choices, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'user_type', 'first_name', 'last_name', 'Company_name',
            'role', 'Street_Address', 'Address_Line_2', 'Country_and_State',
            'Town_City', 'Zip_Code', 'phone_number', 'is_active', 'date_joined'
        ]
        read_only_fields = ('is_active', 'date_joined')

    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if UserProfile.objects.exclude(id=user_id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        try:
            validate_email(value)
        except Exception:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.lower().strip()

    def validate(self, data):
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = UserProfile(**validated_data)
        user.set_unusable_password()  # Password will be set in the view
        user.save()
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


# Keep role-specific serializers but point them to UserProfile (convenience wrappers)
class SuperAdminSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = UserProfile

class ManagerSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = UserProfile

class HRSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = UserProfile

class ExternalUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = UserProfile

class Hiring_managerSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = UserProfile


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        # include only lightweight fields for list endpoints
        fields = ['id', 'email', 'full_name', 'phone_number', 'role']
