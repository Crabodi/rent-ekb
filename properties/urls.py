from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CityViewSet, DistrictViewSet, PropertyViewSet

# Создаем роутер для API
router = DefaultRouter()
router.register(r'cities', CityViewSet, basename='city')
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'properties', PropertyViewSet, basename='property')

urlpatterns = [
    path('', include(router.urls)),
]