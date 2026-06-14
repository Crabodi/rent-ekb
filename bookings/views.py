from django.db import models
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers 
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking, UnavailableDate
from .serializers import (
    BookingSerializer, BookingListSerializer, 
    BookingCreateSerializer, BookingUpdateSerializer,
    BookingForOwnerSerializer, UnavailableDateSerializer
)


class BookingViewSet(viewsets.ModelViewSet):
    """API для работы с бронированиями"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'property_obj', 'rental_type']
    ordering_fields = ['created_at', 'start_date', 'total_price']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        elif self.action == 'for_owner':
            return BookingForOwnerSerializer
        return BookingSerializer
    
    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(
            models.Q(tenant=user) | models.Q(property_obj__owner=user)
        ).distinct()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pending_count(self, request):
        """Возвращает количество ожидающих подтверждения бронирований для текущего пользователя"""
        user = request.user
        
        # Для владельца - заявки на его объекты
        # Для арендатора - его собственные заявки
        pending_bookings = Booking.objects.filter(
            models.Q(tenant=user) | models.Q(property_obj__owner=user),
            status='pending'
        ).distinct()
        
        return Response({'count': pending_bookings.count()})
    
    def perform_create(self, serializer):
        property_obj = serializer.validated_data['property_obj']
        rental_type = serializer.validated_data.get('rental_type')
        
        if rental_type == 'long_term':
            existing_booking = Booking.objects.filter(
                property_obj=property_obj,
                rental_type='long_term',
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing_booking:
                raise serializers.ValidationError(
                    'Этот объект уже забронирован на длительный срок'
                )
        
        booking = serializer.save(tenant=self.request.user)
        self.send_booking_notification_to_owner(booking)
    
    def send_booking_notification_to_owner(self, booking):
        """Отправка уведомления владельцу о новом бронировании"""
        owner = booking.property_obj.owner
        if not owner.email_notifications:
            return
        
        if booking.rental_type == 'daily':
            dates = f"{booking.start_date} - {booking.end_date}"
            nights = booking.nights_count
            period = f"{nights} ночей"
        else:
            dates = f"с {booking.long_term_start_date} (бессрочно)"
            period = "длительная аренда"
        
        subject = f'Новое бронирование на ваш объект "{booking.property_obj.title}"'
        
        message = f"""
Здравствуйте, {owner.username}!

Поступила новая заявка на бронирование вашего объекта "{booking.property_obj.title}".

Детали бронирования:
- Арендатор: {booking.tenant.username}
- Телефон: {booking.tenant.phone}
- Email: {booking.tenant.email}
- Тип аренды: {period}
- Период: {dates}
- Стоимость: {booking.total_price} ₽
- Комментарий арендатора: {booking.tenant_comment or 'Нет комментария'}

Для подтверждения или отмены бронирования перейдите в личный кабинет:
http://127.0.0.1:8000/my-bookings/

С уважением,
Команда Рент.ру
"""
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [owner.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email error to owner: {e}")
    
    def send_booking_status_update_to_tenant(self, booking, status_text, comment=None):
        """Отправка уведомления арендатору об изменении статуса бронирования"""
        tenant = booking.tenant
        if not tenant.email_notifications:
            return
        
        subject = f'Статус бронирования #{booking.id} изменен'
        
        message = f"""
Здравствуйте, {tenant.username}!

Статус вашего бронирования "{booking.property_obj.title}" изменен на: {status_text}

{f'Комментарий владельца: {comment}' if comment else ''}

Детали бронирования можно посмотреть в личном кабинете:
http://127.0.0.1:8000/my-bookings/

С уважением,
Команда Рент.ру
"""
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [tenant.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email error to tenant: {e}")
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Подтверждение бронирования (только для владельца)"""
        booking = self.get_object()
        
        if booking.property_obj.owner != request.user:
            return Response(
                {'error': f'Только владелец может подтвердить бронирование. Вы: {request.user.username}, Владелец: {booking.property_obj.owner.username}'},
                status=status.HTTP_403_FORBIDDEN
            )        
        
        if booking.status != 'pending':
            return Response(
                {'error': f'Нельзя подтвердить бронирование со статусом {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = request.data.get('comment', '')
        
        booking.status = 'confirmed'
        booking.owner_response_comment = comment
        booking.save()
        
        self.send_booking_status_update_to_tenant(booking, 'Подтверждено', comment)
        
        return Response({
            'message': 'Бронирование подтверждено',
            'status': booking.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отмена бронирования (владельцем или арендатором)"""
        booking = self.get_object()
        
        is_owner = booking.property_obj.owner == request.user
        is_tenant = booking.tenant == request.user
        
        if not is_owner and not is_tenant:
            return Response(
                {'error': 'У вас нет прав для отмены этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status == 'completed':
            return Response(
                {'error': 'Завершенное бронирование нельзя отменить'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        comment = request.data.get('comment', '')
        
        booking.status = 'cancelled'
        if is_owner:
            booking.owner_response_comment = comment or reason
        else:
            booking.tenant_comment = comment or reason
        booking.save()
        
        if is_owner:
            self.send_booking_status_update_to_tenant(booking, 'Отменено владельцем', comment)
        else:
            subject = f'Отмена бронирования #{booking.id}'
            message = f"""
Здравствуйте, {booking.property_obj.owner.username}!

Арендатор {booking.tenant.username} отменил бронирование вашего объекта "{booking.property_obj.title}".

{f'Причина: {comment}' if comment else ''}

С уважением,
Команда Рент.ру
"""
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.property_obj.owner.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email error to owner: {e}")
        
        return Response({
            'message': 'Бронирование отменено',
            'status': booking.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel_booking_by_owner(self, request, pk=None):
        """Снятие бронирования владельцем со своего объявления"""
        booking = self.get_object()
        
        if booking.property_obj.owner != request.user:
            return Response(
                {'error': 'Только владелец может снять бронирование со своего объявления'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'confirmed':
            return Response(
                {'error': f'Можно снять только подтвержденное бронирование. Текущий статус: {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.rental_type != 'long_term':
            return Response(
                {'error': 'Снять бронирование можно только для долгосрочной аренды'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = request.data.get('comment', '')
        
        booking.status = 'cancelled'
        booking.owner_response_comment = comment or 'Бронирование снято владельцем'
        booking.save()
        
        property_obj = booking.property_obj
        if not property_obj.is_active:
            property_obj.is_active = True
            property_obj.save()
            print(f"Property {property_obj.title} reactivated")

        self.send_booking_status_update_to_tenant(booking, 'Снято владельцем', comment)
        
        return Response({
            'message': 'Бронирование успешно снято. Объявление снова доступно для аренды.',
            'status': booking.status
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def for_owner(self, request):
        """Получить бронирования для владельца (только ожидающие подтверждения)"""
        user = request.user
        if user.role not in ['landlord', 'both']:
            return Response(
                {'error': 'Только владельцы могут просматривать эту информацию'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bookings = Booking.objects.filter(
            property_obj__owner=user,
            status='pending'
        ).order_by('-created_at')
        
        serializer = BookingForOwnerSerializer(bookings, many=True)
        return Response(serializer.data)