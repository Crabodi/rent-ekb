from rest_framework import serializers
from .models import Booking, UnavailableDate
from properties.serializers import PropertyListSerializer
from users.serializers import UserSerializer


class UnavailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnavailableDate
        fields = ['id', 'date', 'reason']


class BookingSerializer(serializers.ModelSerializer):
    """Полный сериализатор бронирования"""
    property_details = PropertyListSerializer(source='property_obj', read_only=True)
    tenant_details = UserSerializer(source='tenant', read_only=True)
    duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property_obj', 'property_details', 'tenant', 'tenant_details',
            'start_date', 'end_date', 'total_price', 'status', 
            'contract_signed', 'contract_file', 'tenant_comment',
            'duration_days', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']


class BookingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка бронирований"""
    property_title = serializers.CharField(source='property_obj.title', read_only=True)
    property_main_image = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.username', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property_obj', 'property_title', 'property_main_image',
            'tenant', 'tenant_name', 'start_date', 'end_date', 
            'total_price', 'status', 'created_at'
        ]
    
    def get_property_main_image(self, obj):
        if obj.property_obj.main_image:
            return obj.property_obj.main_image
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бронирования"""
    class Meta:
        model = Booking
        fields = [
            'property_obj', 'start_date', 'end_date', 'tenant_comment'
        ]
    
    def validate(self, data):
        """Проверка доступности дат"""
        property_obj = data['property_obj']
        start_date = data['start_date']
        end_date = data['end_date']
        
        # Проверяем, что даты не в прошлом
        from datetime import date
        if start_date < date.today():
            raise serializers.ValidationError('Дата заезда не может быть в прошлом')
        
        if start_date >= end_date:
            raise serializers.ValidationError('Дата заезда должна быть раньше даты выезда')
        
        # Проверяем пересечение с существующими бронированиями
        conflicting = Booking.objects.filter(
            property_obj=property_obj,
            status__in=['pending', 'confirmed'],
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        if conflicting.exists():
            raise serializers.ValidationError(
                'Выбранные даты уже заняты. Пожалуйста, выберите другие даты.'
            )
        
        return data