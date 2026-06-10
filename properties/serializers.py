from rest_framework import serializers
from .models import City, District, Property, PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    """Сериализатор для фотографий"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'title', 'is_main', 'order']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


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
    owner_avatar = serializers.ImageField(source='owner.avatar', read_only=True)
    price_display = serializers.ReadOnlyField()
    location_display = serializers.ReadOnlyField()
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'rooms', 
            'city_name', 'district_name', 'price_display',
            'location_display', 'main_image', 'owner_name',
            'owner_avatar', 'created_at'
        ]
    
    def get_main_image(self, obj):
        """Получить URL главного изображения"""
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image)
            return obj.main_image
        return None


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра"""
    city = CitySerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_avatar = serializers.ImageField(source='owner.avatar', read_only=True)
    price_display = serializers.ReadOnlyField()
    location_display = serializers.ReadOnlyField()
    images = PropertyImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'rooms', 'city', 'district',
            'address', 'description', 'rental_term', 'price_per_day',
            'price_per_month', 'owner', 'owner_name', 'owner_phone',
            'owner_email', 'owner_avatar', 'price_display', 'location_display',
            'images', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']


class PropertyCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования"""
    class Meta:
        model = Property
        fields = [
            'title', 'property_type', 'rooms', 'city', 'district',
            'description', 'address', 'rental_term', 'price_per_day',
            'price_per_month'
        ]
    
    def validate(self, data):
        # Проверка цены в зависимости от типа аренды
        rental_term = data.get('rental_term')
        
        if rental_term == 'daily' and not data.get('price_per_day'):
            raise serializers.ValidationError({
                'price_per_day': 'Для посуточной аренды укажите цену за сутки'
            })
        
        if rental_term == 'long_term' and not data.get('price_per_month'):
            raise serializers.ValidationError({
                'price_per_month': 'Для длительной аренды укажите цену за месяц'
            })
        
        if rental_term == 'both':
            if not data.get('price_per_day') and not data.get('price_per_month'):
                raise serializers.ValidationError(
                    'Укажите хотя бы одну цену: за сутки или за месяц'
                )
        
        # Проверка количества комнат
        rooms = data.get('rooms')
        if rooms and rooms < 1:
            raise serializers.ValidationError({
                'rooms': 'Количество комнат должно быть не менее 1'
            })
        
        return data
    
    def create(self, validated_data):
        # Автоматически устанавливаем владельца из контекста запроса
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['owner'] = request.user
        return super().create(validated_data)