from rest_framework import serializers
from django.db import transaction
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at']

    def validate_name(self, value):
        # We use Category instead of category (case sensitive matching depends on DB, but unique=True in model handles most cases)
        if Category.objects.filter(name__iexact=value).exists():
            if self.instance and self.instance.name.lower() == value.lower():
                return value
            raise serializers.ValidationError("Category with this name already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        return Category.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
