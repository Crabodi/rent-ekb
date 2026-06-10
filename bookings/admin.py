from django.contrib import admin
from .models import Booking, UnavailableDate

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'property_obj', 'tenant', 'start_date', 'end_date', 'total_price', 'status')
    list_filter = ('status', 'contract_signed', 'created_at')
    search_fields = ('property_obj__title', 'tenant__username', 'tenant__email')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    list_per_page = 20
    
    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('property_obj', 'tenant', 'start_date', 'end_date')
        }),
        ('Финансы и статус', {
            'fields': ('total_price', 'status', 'contract_signed', 'contract_file')
        }),
        ('Комментарии', {
            'fields': ('tenant_comment', 'owner_comment')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(UnavailableDate)
class UnavailableDateAdmin(admin.ModelAdmin):
    list_display = ('property_obj', 'date', 'reason', 'created_at')
    list_filter = ('property_obj',)
    search_fields = ('property_obj__title', 'reason')
    list_per_page = 20