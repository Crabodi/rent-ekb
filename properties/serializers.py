from rest_framework import serializers
from .models import City, District, Property

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'is_active']

class DistrictSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'city', 'city_name']

class PropertyListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка объектов"""
    city_name = serializers.CharField(source='city.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    price_display = serializers.ReadOnlyField()
    location_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'rooms', 
            'city_name', 'district_name', 'price_display',
            'location_display', 'photos', 'created_at'
        ]

class PropertyDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра"""
    city = CitySerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)
    price_display = serializers.ReadOnlyField()
    location_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

class PropertyCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования"""
    class Meta:
        model = Property
        fields = [
            'title', 'property_type', 'rooms', 'city', 'district',
            'description', 'address', 'rental_term', 'price_per_day',
            'price_per_month', 'photos'
        ]
    
    def validate(self, data):
        # Проверка цены в зависимости от типа аренды
        if data['rental_term'] == 'daily' and not data.get('price_per_day'):
            raise serializers.ValidationError("Для посуточной аренды укажите цену за сутки")
        if data['rental_term'] == 'long_term' and not data.get('price_per_month'):
            raise serializers.ValidationError("Для длительной аренды укажите цену за месяц")
        return data