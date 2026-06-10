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
    PropertyCreateSerializer
)


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
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyCreateSerializer
        return PropertyDetailSerializer
    
    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def get_queryset(self):
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
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_properties(self, request):
        """Получить объявления текущего пользователя"""
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
        
        # Проверяем, что пользователь - владелец
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