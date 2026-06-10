from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Booking, UnavailableDate
from .serializers import (
    BookingSerializer, BookingListSerializer, 
    BookingCreateSerializer, UnavailableDateSerializer
)


class BookingViewSet(viewsets.ModelViewSet):
    """API для работы с бронированиями"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'property_obj', 'start_date', 'end_date']
    ordering_fields = ['created_at', 'start_date', 'total_price']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Владелец видит бронирования своих объектов
        if user.role in ['landlord', 'both']: # type: ignore
            return Booking.objects.filter(property_obj__owner=user)
        # Арендатор видит свои бронирования
        return Booking.objects.filter(tenant=user)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Подтверждение бронирования (только для владельца)"""
        booking = self.get_object()
        
        # Проверяем, что пользователь - владелец объекта
        if booking.property_obj.owner != request.user:
            return Response(
                {'error': 'Только владелец может подтвердить бронирование'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {'error': f'Нельзя подтвердить бронирование со статусом {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.save()
        
        # TODO: Отправить email уведомление
        return Response({'message': 'Бронирование подтверждено'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена бронирования"""
        booking = self.get_object()
        
        # Проверяем права (отменить может арендатор или владелец)
        if booking.tenant != request.user and booking.property_obj.owner != request.user:
            return Response(
                {'error': 'У вас нет прав для отмены этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status == 'completed':
            return Response(
                {'error': 'Завершенное бронирование нельзя отменить'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        # TODO: Отправить email уведомление
        return Response({'message': 'Бронирование отменено'})