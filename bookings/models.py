from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from properties.models import Property

class Booking(models.Model):
    """
    Модель бронирования объекта недвижимости
    """
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    # Связи
    property_obj = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        verbose_name='Объект недвижимости'
    )
    
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        verbose_name='Арендатор'
    )
    
    # Даты бронирования
    start_date = models.DateField('Дата заезда')
    end_date = models.DateField('Дата выезда')
    
    # Финансы
    total_price = models.DecimalField(
        'Общая стоимость', 
        max_digits=10, 
        decimal_places=2,
        help_text='Автоматически рассчитывается'
    )
    
    # Статус
    status = models.CharField(
        'Статус', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    # Договор
    contract_signed = models.BooleanField('Договор подписан', default=False)
    contract_file = models.FileField(
        'Файл договора', 
        upload_to='contracts/%Y/%m/%d/', 
        null=True, 
        blank=True
    )
    
    # Комментарии
    tenant_comment = models.TextField('Комментарий арендатора', blank=True)
    owner_comment = models.TextField('Комментарий владельца', blank=True)
    
    # Системные поля
    created_at = models.DateTimeField('Дата бронирования', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    def clean(self):
        """Валидация дат"""
        if self.start_date >= self.end_date:
            raise ValidationError('Дата заезда должна быть раньше даты выезда')
        
        if self.start_date < models.DateField().auto_now: # type: ignore
            raise ValidationError('Дата заезда не может быть в прошлом')
    
    def save(self, *args, **kwargs):
        """Автоматический расчет стоимости при сохранении"""
        if not self.total_price:
            if self.property_obj.rental_term in ['daily', 'both'] and self.property_obj.price_per_day:
                # Посуточная аренда
                days = (self.end_date - self.start_date).days
                self.total_price = days * self.property_obj.price_per_day
            elif self.property_obj.rental_term == 'long_term' and self.property_obj.price_per_month:
                # Длительная аренда (в месяцах)
                months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
                months = max(months, 1)  # Минимум 1 месяц
                self.total_price = months * self.property_obj.price_per_month
        
        self.full_clean()  # Проверяем валидацию перед сохранением
        super().save(*args, **kwargs)
    
    @property
    def duration_days(self):
        """Количество дней аренды"""
        return (self.end_date - self.start_date).days
    
    @property
    def duration_months(self):
        """Количество месяцев аренды"""
        return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
    
    def __str__(self):
        return f"Бронь #{self.id} - {self.property_obj.title} ({self.tenant.username})" # type: ignore
    
    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']
        # Защита от двойного бронирования
        unique_together = ['property_obj', 'start_date', 'end_date']

class UnavailableDate(models.Model):
    """
    Модель занятых дат для посуточной аренды
    """
    property_obj = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='unavailable_dates',
        verbose_name='Объект недвижимости'
    )
    
    date = models.DateField('Недоступная дата')
    
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='unavailable_dates',
        null=True,
        blank=True,
        verbose_name='Бронирование'
    )
    
    reason = models.CharField(
        'Причина',
        max_length=200,
        blank=True,
        help_text='Например: "Технические работы" или "Владелец занят"'
    )
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    def __str__(self):
        return f"{self.property_obj.title} - {self.date}"
    
    class Meta:
        verbose_name = 'Недоступная дата'
        verbose_name_plural = 'Недоступные даты'
        ordering = ['date']
        unique_together = ['property_obj', 'date']  # Дата может быть занята только один раз