from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер для API
router = DefaultRouter()
# Если у вас есть ViewSet для бронирований, раскомментируйте:
# router.register(r'bookings', views.BookingViewSet, basename='booking')

urlpatterns = [
    # Временный маршрут для проверки
    path('test/', views.test_view, name='test'),
    
    # Включаем роутер
    path('', include(router.urls)),
]