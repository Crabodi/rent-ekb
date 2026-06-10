from django.contrib import admin
from .models import City, District, Property

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    list_filter = ('city',)
    search_fields = ('name', 'city__name')
    autocomplete_fields = ('city',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'district', 'property_type', 'rooms', 'rental_term', 'is_active')
    list_filter = ('property_type', 'rental_term', 'city', 'district', 'is_active')
    search_fields = ('title', 'address', 'owner__username', 'city__name', 'district__name')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('city', 'district')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('owner', 'title', 'property_type', 'rooms', 'description', 'address')
        }),
        ('Локация', {
            'fields': ('city', 'district')
        }),
        ('Условия аренды', {
            'fields': ('rental_term', 'price_per_day', 'price_per_month')
        }),
        ('Дополнительно', {
            'fields': ('photos', 'is_active', 'created_at', 'updated_at')
        }),
    )