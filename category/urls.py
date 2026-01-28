from django.urls import path
from .views import CategoryAPIView

urlpatterns = [
    path('', CategoryAPIView.as_view(), name='category-list-create'),
    path('<int:pk>/', CategoryAPIView.as_view(), name='category-detail'),
]
