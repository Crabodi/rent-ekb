from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import City, District, Property
from .serializers import (
    CitySerializer, DistrictSerializer, 
    PropertyListSerializer, PropertyDetailSerializer, 
    PropertyCreateSerializer, PropertyUpdateSerializer
)
from bookings.models import Booking


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с городами"""
    queryset = City.objects.filter(is_active=True)
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    """API для работы с районами"""
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    
    def get_queryset(self):
        queryset = District.objects.all()
        city_id = self.request.GET.get('city', None)
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        return queryset


class PropertyViewSet(viewsets.ModelViewSet):
    """API для работы с объектами недвижимости"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'rooms', 'city', 'district', 'rental_term', 'is_active']
    search_fields = ['title', 'description', 'address']
    ordering_fields = ['price_per_day', 'price_per_month', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        elif self.action == 'create':
            return PropertyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PropertyUpdateSerializer
        return PropertyDetailSerializer
    
    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def get_queryset(self):
        user = self.request.user
        is_landlord = user.is_authenticated and user.role in ['landlord', 'both'] # type: ignore
        
        # Базовый queryset - только активные объявления
        queryset = Property.objects.filter(is_active=True)
        
        # Фильтрация по цене
        min_price = self.request.GET.get('min_price', None)
        max_price = self.request.GET.get('max_price', None)
        
        if min_price:
            queryset = queryset.filter(
                models.Q(price_per_day__gte=min_price) | 
                models.Q(price_per_month__gte=min_price)
            )
        if max_price:
            queryset = queryset.filter(
                models.Q(price_per_day__lte=max_price) | 
                models.Q(price_per_month__lte=max_price)
            )
        
        # Фильтрация по параметрам запроса
        property_type = self.request.GET.get('property_type', None)
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        rooms = self.request.GET.get('rooms', None)
        if rooms:
            queryset = queryset.filter(rooms=rooms)
        
        city = self.request.GET.get('city', None)
        if city:
            queryset = queryset.filter(city_id=city)
        
        district = self.request.GET.get('district', None)
        if district:
            queryset = queryset.filter(district_id=district)
        
        rental_term = self.request.GET.get('rental_term', None)
        if rental_term:
            queryset = queryset.filter(rental_term=rental_term)
        
        # Для не-владельцев: исключаем долгосрочные объекты, которые уже забронированы
        if not is_landlord:
            booked_long_term_ids = Booking.objects.filter(
                rental_type='long_term',
                status__in=['pending', 'confirmed']
            ).values_list('property_obj_id', flat=True)
            
            queryset = queryset.exclude(
                models.Q(rental_term='long_term') & models.Q(id__in=booked_long_term_ids)
            )
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Получение одного объекта - всегда доступно для владельца"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_properties(self, request):
        """Получить объявления текущего пользователя (все, без фильтрации)"""
        properties = Property.objects.filter(owner=request.user)
        serializer = PropertyListSerializer(
            properties, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_active(self, request, pk=None):
        """Включить/выключить активность объявления"""
        property_obj = self.get_object()
        
        if property_obj.owner != request.user:
            return Response(
                {'error': 'Вы не являетесь владельцем этого объекта'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        property_obj.is_active = not property_obj.is_active
        property_obj.save()
        
        return Response({
            'id': property_obj.id,
            'is_active': property_obj.is_active,
            'message': 'Статус объявления обновлен'
        })
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_photo(self, request, pk=None):
        """Удалить фотографию объявления"""
        property_obj = self.get_object()
        
        if property_obj.owner != request.user:
            return Response(
                {'error': 'Вы не являетесь владельцем этого объекта'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        photo_id = request.data.get('photo_id')
        if not photo_id:
            return Response(
                {'error': 'Не указан ID фотографии'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .models import PropertyImage
            photo = PropertyImage.objects.get(id=photo_id, property_obj=property_obj)
            photo.delete()
            return Response({'message': 'Фотография удалена'})
        except PropertyImage.DoesNotExist:
            return Response(
                {'error': 'Фотография не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )