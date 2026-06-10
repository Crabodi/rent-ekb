from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone')
    
    # Добавляем новые поля в форму редактирования
    fieldsets = list(UserAdmin.fieldsets) + [
        ('Контактная информация', {
            'fields': ('phone', 'avatar', 'telegram_id')
        }),
        ('Дополнительная информация', {
            'fields': ('role', 'bio', 'email_notifications', 'email_verified')
        }),
    ]
    
    # Поля при создании нового пользователя
    add_fieldsets = list(UserAdmin.add_fieldsets) + [
        ('Контактная информация', {
            'fields': ('email', 'phone', 'role')
        }),
    ]