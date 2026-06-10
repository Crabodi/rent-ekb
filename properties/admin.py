from django.contrib import admin
from django.utils.html import format_html
from .models import City, District, Property, PropertyImage

class PropertyImageInline(admin.TabularInline):
    """Встроенная форма для загрузки фотографий прямо в объявлении"""
    model = PropertyImage
    extra = 5  # Показывать 5 пустых полей для загрузки
    fields = ('image', 'title', 'is_main', 'order', 'preview')
    readonly_fields = ('preview',)
    
    def preview(self, obj):
        """Превью фотографии в админке"""
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.image.url)
        return "Нет фото"
    preview.short_description = 'Превью'

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)
    list_per_page = 20

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    list_filter = ('city',)
    search_fields = ('name', 'city__name')
    autocomplete_fields = ('city',)
    list_per_page = 20

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'city', 'district', 'property_type', 'rooms', 'rental_term', 'is_active', 'main_image_preview')
    list_filter = ('property_type', 'rental_term', 'city', 'district', 'is_active')
    search_fields = ('title', 'address', 'owner__username', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('owner', 'city', 'district')
    list_per_page = 20
    inlines = [PropertyImageInline]  # Добавляем фотографии прямо в форму объявления
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('owner', 'title', 'property_type', 'rooms', 'description')
        }),
        ('Локация', {
            'fields': ('city', 'district', 'address')
        }),
        ('Условия аренды', {
            'fields': ('rental_term', 'price_per_day', 'price_per_month')
        }),
        ('Статус', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def main_image_preview(self, obj):
        """Показываем главное фото в списке объявлений"""
        if obj.main_image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.main_image)
        return "Нет фото"
    main_image_preview.short_description = 'Главное фото'

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'property_obj', 'is_main', 'order', 'uploaded_at', 'preview')
    list_filter = ('is_main', 'property_obj')
    list_editable = ('is_main', 'order')
    readonly_fields = ('preview',)
    
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.image.url)
        return "Нет фото"
    preview.short_description = 'Превью'