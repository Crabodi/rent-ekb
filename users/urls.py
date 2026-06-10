from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

# Создаем роутер для API
router = DefaultRouter()
# Если у вас есть ViewSet для пользователей, раскомментируйте:
# router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # JWT аутентификация
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Регистрация и профиль
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Включаем роутер
    path('', include(router.urls)),
]