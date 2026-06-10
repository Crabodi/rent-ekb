from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class City(models.Model):
    """Модель города"""
    name = models.CharField('Название города', max_length=100)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']

class District(models.Model):
    """Районы города"""
    name = models.CharField('Название района', max_length=100)
    city = models.ForeignKey(
        City, 
        on_delete=models.CASCADE, 
        related_name='districts',
        verbose_name='Город'
    )
    
    def __str__(self):
        return f"{self.name} ({self.city.name})"
    
    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'
        unique_together = ['name', 'city']  # Один район не может быть в двух городах

class Property(models.Model):
    """Модель объекта недвижимости"""
    
    PROPERTY_TYPES = [
        ('apartment', 'Квартира'),
        ('room', 'Комната'),
        ('house', 'Дом'),
    ]
    
    RENTAL_TERMS = [
        ('daily', 'Посуточно'),
        ('long_term', 'Длительная'),
    ]
    
    # Основная информация
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='properties',
        verbose_name='Владелец'
    )
    title = models.CharField('Заголовок', max_length=200)
    property_type = models.CharField('Тип объекта', max_length=20, choices=PROPERTY_TYPES)
    rooms = models.IntegerField('Количество комнат', validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Локация
    city = models.ForeignKey(
        City, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='properties',
        verbose_name='Город'
    )
    district = models.ForeignKey(
        District, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='properties',
        verbose_name='Район'
    )
    
    # Описание
    description = models.TextField('Описание')
    address = models.CharField('Адрес', max_length=300)
    
    # Условия аренды
    rental_term = models.CharField('Срок аренды', max_length=20, choices=RENTAL_TERMS)
    price_per_day = models.DecimalField('Цена за сутки', max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField('Цена за месяц', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Дополнительная информация
    photos = models.JSONField('Фотографии', default=list)  # Список URL фотографий
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.city.name if self.city else 'Город не указан'}"
    
    @property
    def price_display(self):
        """Отображение цены в зависимости от срока аренды"""
        if self.rental_term == 'daily' and self.price_per_day:
            return f"{self.price_per_day} ₽/сутки"
        elif self.rental_term == 'long_term' and self.price_per_month:
            return f"{self.price_per_month} ₽/месяц"
        return "Цена не указана"
    
    @property
    def location_display(self):
        """Отображение локации"""
        if self.district:
            return f"{self.city.name}, {self.district.name}" # type: ignore
        elif self.city:
            return self.city.name
        return "Локация не указана"
    
    class Meta:
        verbose_name = 'Объект недвижимости'
        verbose_name_plural = 'Объекты недвижимости'
        ordering = ['-created_at']