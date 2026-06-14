from rest_framework import serializers
from .models import Booking, UnavailableDate
from properties.serializers import PropertyListSerializer
from users.serializers import UserSerializer
from datetime import date


class UnavailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnavailableDate
        fields = ['id', 'date', 'reason']


class BookingSerializer(serializers.ModelSerializer):
    """Полный сериализатор бронирования"""
    property_details = PropertyListSerializer(source='property_obj', read_only=True)
    tenant_details = UserSerializer(source='tenant', read_only=True)
    duration_days = serializers.ReadOnlyField()
    display_dates = serializers.ReadOnlyField()
    is_long_term = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property_obj', 'property_details', 'tenant', 'tenant_details',
            'rental_type', 'start_date', 'end_date', 'nights_count',
            'long_term_start_date', 'total_price', 'status', 
            'contract_signed', 'contract_file', 'tenant_comment', 'owner_comment',
            'owner_response_comment',  # Добавляем новое поле
            'duration_days', 'display_dates', 'is_long_term',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']


class BookingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка бронирований"""
    property_title = serializers.CharField(source='property_obj.title', read_only=True)
    property_main_image = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.username', read_only=True)
    display_dates = serializers.ReadOnlyField()
    rental_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property_obj', 'property_title', 'property_main_image',
            'tenant', 'tenant_name', 'rental_type', 'rental_type_display',
            'start_date', 'end_date', 'long_term_start_date',
            'total_price', 'status', 'display_dates', 'created_at',
            'owner_response_comment'  # Добавляем для отображения ответа владельца
        ]
    
    def get_property_main_image(self, obj):
        if obj.property_obj and obj.property_obj.main_image:
            return obj.property_obj.main_image
        return None
    
    def get_rental_type_display(self, obj):
        return 'Посуточно' if obj.rental_type == 'daily' else 'Длительная (бессрочно)'


class BookingCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бронирования"""
    
    class Meta:
        model = Booking
        fields = [
            'property_obj', 'rental_type', 'start_date', 'end_date',
            'nights_count', 'long_term_start_date', 'tenant_comment'
        ]
    
    def validate(self, data):
        """Проверка доступности в зависимости от типа аренды"""
        property_obj = data['property_obj']
        rental_type = data.get('rental_type')
        
        # Проверяем соответствие типа аренды объявлению
        if property_obj.rental_term == 'daily' and rental_type != 'daily':
            raise serializers.ValidationError(
                'Это объявление только для посуточной аренды'
            )
        
        if property_obj.rental_term == 'long_term' and rental_type != 'long_term':
            raise serializers.ValidationError(
                'Это объявление только для долгосрочной аренды'
            )
        
        # Валидация для посуточной аренды
        if rental_type == 'daily':
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            nights_count = data.get('nights_count')
            
            if not start_date or not end_date:
                raise serializers.ValidationError(
                    'Укажите даты заезда и выезда'
                )
            
            if start_date < date.today():
                raise serializers.ValidationError(
                    'Дата заезда не может быть в прошлом'
                )
            
            if start_date >= end_date:
                raise serializers.ValidationError(
                    'Дата заезда должна быть раньше даты выезда'
                )
            
            # Проверяем, что количество ночей соответствует датам
            calculated_nights = (end_date - start_date).days
            if nights_count and nights_count != calculated_nights:
                data['nights_count'] = calculated_nights
            
            # Проверяем пересечение с существующими бронированиями
            conflicting = Booking.objects.filter(
                property_obj=property_obj,
                rental_type='daily',
                status__in=['pending', 'confirmed'],
                start_date__lt=end_date,
                end_date__gt=start_date
            )
            
            if conflicting.exists():
                raise serializers.ValidationError(
                    'Выбранные даты уже заняты. Пожалуйста, выберите другие даты.'
                )
        
        # Валидация для долгосрочной аренды
        elif rental_type == 'long_term':
            long_term_start_date = data.get('long_term_start_date')
            
            if not long_term_start_date:
                raise serializers.ValidationError(
                    'Укажите дату начала аренды'
                )
            
            if long_term_start_date < date.today():
                raise serializers.ValidationError(
                    'Дата начала аренды не может быть в прошлом'
                )
            
            # Проверяем, не забронирован ли объект уже на длительный срок
            active_long_term = Booking.objects.filter(
                property_obj=property_obj,
                rental_type='long_term',
                status__in=['pending', 'confirmed']
            ).exclude(status='cancelled')
            
            if active_long_term.exists():
                raise serializers.ValidationError(
                    'Этот объект уже забронирован на длительный срок'
                )
        
        return data
    
    def create(self, validated_data):
        """Создание бронирования с автоматическим расчетом"""
        rental_type = validated_data.get('rental_type')
        
        # Для посуточной аренды рассчитываем nights_count
        if rental_type == 'daily':
            start_date = validated_data.get('start_date')
            end_date = validated_data.get('end_date')
            if start_date and end_date:
                validated_data['nights_count'] = (end_date - start_date).days
        
        # Для долгосрочной аренды устанавливаем start_date = long_term_start_date
        elif rental_type == 'long_term':
            long_term_start_date = validated_data.get('long_term_start_date')
            if long_term_start_date:
                validated_data['start_date'] = long_term_start_date
        
        return super().create(validated_data)


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления статуса бронирования"""
    
    class Meta:
        model = Booking
        fields = ['status', 'owner_comment', 'owner_response_comment', 'contract_signed', 'contract_file']
    
    def validate_status(self, value):
        allowed_statuses = ['confirmed', 'cancelled', 'completed']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f'Статус может быть изменен только на: {", ".join(allowed_statuses)}'
            )
        return value


class BookingForOwnerSerializer(serializers.ModelSerializer):
    """Сериализатор для владельца (список бронирований его объектов)"""
    property_title = serializers.CharField(source='property_obj.title', read_only=True)
    property_address = serializers.CharField(source='property_obj.address', read_only=True)
    tenant_name = serializers.CharField(source='tenant.username', read_only=True)
    tenant_phone = serializers.CharField(source='tenant.phone', read_only=True)
    tenant_email = serializers.EmailField(source='tenant.email', read_only=True)
    display_dates = serializers.ReadOnlyField()
    rental_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property_obj', 'property_title', 'property_address',
            'tenant', 'tenant_name', 'tenant_phone', 'tenant_email',
            'rental_type', 'rental_type_display', 'start_date', 'end_date',
            'long_term_start_date', 'total_price', 'status', 'tenant_comment',
            'owner_comment', 'owner_response_comment', 'display_dates',
            'created_at'
        ]
    
    def get_rental_type_display(self, obj):
        return 'Посуточно' if obj.rental_type == 'daily' else 'Длительная (бессрочно)'