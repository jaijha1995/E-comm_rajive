from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Category
from .serializers import CategorySerializer
from superadmin.permission import CanCreateCategory


class CategoryAPIView(APIView):
    # 🔐 Authentication only for protected methods
    def get_authenticators(self):
        if self.request.method in ["POST", "PATCH", "DELETE"]:
            return [JWTAuthentication()]
        return []

    # 🔐 Permission only for protected methods
    def get_permissions(self):
        if self.request.method in ["POST", "PATCH", "DELETE"]:
            return [CanCreateCategory()]
        return [permissions.AllowAny()]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    # 🔓 GET (List or Detail)
    def get(self, request, pk=None):
        if pk:
            category = self.get_object(pk)
            if not category:
                return Response({
                    "status": "error",
                    "message": "Category not found"
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = CategorySerializer(category)
            return Response({
                "status": "success",
                "message": "Category retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response({
            "status": "success",
            "message": "Categories retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # 🔒 POST (Create)
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Category created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🔒 PATCH (Update)
    def patch(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({
                "status": "error",
                "message": "Category not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Category updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # 🔒 DELETE
    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({
                "status": "error",
                "message": "Category not found"
            }, status=status.HTTP_404_NOT_FOUND)

        category.delete()
        return Response({
            "status": "success",
            "message": "Category deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)
