"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # API маршруты
    path('api/', include('properties.urls')),  
    path('api/users/', include('users.urls')),  
    path('api/bookings/', include('bookings.urls')), 

    # Фронтенд маршруты
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('my-properties/', views.MyPropertiesView.as_view(), name='my_properties'),
    path('my-bookings/', views.MyBookingsView.as_view(), name='my_bookings'),
    path('property/<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('property/create/', views.CreatePropertyView.as_view(), name='create_property'),

    path('how-to-rent-out/', views.HowToRentOutView.as_view(), name='how_to_rent_out'),  
    path('how-to-rent/', views.HowToRentView.as_view(), name='how_to_rent'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)