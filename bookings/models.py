from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from properties.models import Property
from datetime import date

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
    
    RENTAL_TYPE_CHOICES = [
        ('daily', 'Посуточно'),
        ('long_term', 'Длительная'),
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
    
    # Тип аренды
    rental_type = models.CharField(
        'Тип аренды',
        max_length=20,
        choices=RENTAL_TYPE_CHOICES,
        default='daily'
    )
    
    # Для посуточной аренды
    start_date = models.DateField(
        'Дата заезда',
        null=True,
        blank=True,
        help_text='Для посуточной аренды'
    )
    end_date = models.DateField(
        'Дата выезда',
        null=True,
        blank=True,
        help_text='Для посуточной аренды'
    )
    nights_count = models.IntegerField(
        'Количество ночей',
        null=True,
        blank=True,
        help_text='Для посуточной аренды'
    )
    
    # Для долгосрочной аренды
    long_term_start_date = models.DateField(
        'Дата начала долгосрочной аренды',
        null=True,
        blank=True,
        help_text='Для долгосрочной аренды (бессрочно)'
    )
    
    # Финансы
    total_price = models.DecimalField(
        'Общая стоимость', 
        max_digits=10, 
        decimal_places=2,
        help_text='Для посуточной - общая сумма, для долгосрочной - цена за месяц'
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
    owner_response_comment = models.TextField(  # НОВОЕ ПОЛЕ
        'Комментарий владельца при ответе',
        blank=True,
        help_text='Комментарий при подтверждении или отказе бронирования'
    )
    
    # Системные поля
    created_at = models.DateTimeField('Дата бронирования', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    def clean(self):
        """Валидация дат"""
        if self.rental_type == 'daily':
            if self.start_date and self.end_date:
                if self.start_date >= self.end_date:
                    raise ValidationError('Дата заезда должна быть раньше даты выезда')
                
                if self.start_date < date.today():
                    raise ValidationError('Дата заезда не может быть в прошлом')
        
        elif self.rental_type == 'long_term':
            if self.long_term_start_date and self.long_term_start_date < date.today():
                raise ValidationError('Дата начала аренды не может быть в прошлом')
    
    def save(self, *args, **kwargs):
        """Автоматический расчет стоимости при сохранении"""
        if not self.total_price:
            if self.rental_type == 'daily' and self.nights_count and self.property_obj.price_per_day:
                # Посуточная аренда
                self.total_price = self.nights_count * self.property_obj.price_per_day
            elif self.rental_type == 'long_term' and self.property_obj.price_per_month:
                # Долгосрочная аренда - цена за месяц
                self.total_price = self.property_obj.price_per_month
        
        self.full_clean()  # Проверяем валидацию перед сохранением
        super().save(*args, **kwargs)
    
    @property
    def duration_days(self):
        """Количество дней аренды (только для посуточной)"""
        if self.rental_type == 'daily' and self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    @property
    def is_long_term(self):
        """Проверка, является ли бронирование долгосрочным"""
        return self.rental_type == 'long_term'
    
    @property
    def display_dates(self):
        """Форматированное отображение дат"""
        if self.rental_type == 'daily':
            if self.start_date and self.end_date:
                return f"{self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}"
        elif self.rental_type == 'long_term':
            if self.long_term_start_date:
                return f"с {self.long_term_start_date.strftime('%d.%m.%Y')} (бессрочно)"
        return "Даты не указаны"
    
    def __str__(self):
        rental_type_str = 'посуточно' if self.rental_type == 'daily' else 'длительная'
        return f"Бронь #{self.id} - {self.property_obj.title} ({rental_type_str})"  # type: ignore
    
    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']


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
        unique_together = ['property_obj', 'date']