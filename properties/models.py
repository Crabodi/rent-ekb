from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class City(models.Model):
    """Модель города, где находится недвижимость"""
    name = models.CharField('Название города', max_length=100, unique=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']


class District(models.Model):
    """Модель района в городе"""
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
        ordering = ['city__name', 'name']
        unique_together = ['name', 'city']


class PropertyImage(models.Model):
    """Модель для фотографий объекта недвижимости"""
    property_obj = models.ForeignKey(
        'Property',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Объект недвижимости'
    )
    image = models.ImageField(
        'Фотография',
        upload_to='properties/%Y/%m/%d/',
        help_text='Загрузите фотографию объекта'
    )
    title = models.CharField(
        'Название фото',
        max_length=100,
        blank=True,
        help_text='Необязательное описание фото'
    )
    is_main = models.BooleanField(
        'Главное фото',
        default=False,
        help_text='Отметьте, если это главное фото объявления'
    )
    order = models.PositiveIntegerField(
        'Порядок',
        default=0,
        help_text='Порядок отображения фотографий'
    )
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Если это главное фото, снимаем флаг с других фото этого объекта
        if self.is_main:
            PropertyImage.objects.filter(
                property_obj=self.property_obj, 
                is_main=True
            ).update(is_main=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Фото {self.property_obj.title} - {self.id}" # type: ignore
    
    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'
        ordering = ['order', 'uploaded_at']


class Property(models.Model):
    """Модель объекта недвижимости"""
    
    PROPERTY_TYPES = [
        ('apartment', 'Квартира'),
        ('room', 'Комната'),
        ('house', 'Дом'),
        ('studio', 'Студия'),
    ]
    
    RENTAL_TERMS = [
        ('daily', 'Посуточно'),
        ('long_term', 'Длительная'),
        ('both', 'Оба варианта'),
    ]
    
    # Основная информация
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='properties',
        verbose_name='Владелец'
    )
    
    title = models.CharField(
        'Заголовок объявления', 
        max_length=200,
        help_text='Например: "Уютная квартира в центре"'
    )
    
    property_type = models.CharField(
        'Тип объекта', 
        max_length=20, 
        choices=PROPERTY_TYPES
    )
    
    rooms = models.IntegerField(
        'Количество комнат', 
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
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
        blank=True,
        related_name='properties',
        verbose_name='Район'
    )
    
    address = models.CharField(
        'Полный адрес', 
        max_length=300,
        help_text='Улица, номер дома'
    )
    
    # Описание
    description = models.TextField(
        'Описание',
        help_text='Опишите все особенности объекта'
    )
    
    # Условия аренды
    rental_term = models.CharField(
        'Срок аренды', 
        max_length=20, 
        choices=RENTAL_TERMS,
        default='both'
    )
    
    price_per_day = models.DecimalField(
        'Цена за сутки (₽)', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Для посуточной аренды'
    )
    
    price_per_month = models.DecimalField(
        'Цена за месяц (₽)', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Для длительной аренды'
    )
    
    
    is_active = models.BooleanField(
        'Активно', 
        default=True,
        help_text='Отметьте, если объявление активно'
    )
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.city.name if self.city else 'Город не указан'}"
    
    @property
    def main_image(self):
        """Получить главное фото объекта"""
        main = self.images.filter(is_main=True).first() # type: ignore
        if main:
            return main.image.url
        first = self.images.first() # type: ignore
        if first:
            return first.image.url
        return None
    
    @property
    def all_images(self):
        """Получить все фото объекта"""
        return self.images.all() # type: ignore
    
    @property
    def price_display(self):
        """Красивое отображение цены"""
        if self.rental_term == 'daily' and self.price_per_day:
            return f"{self.price_per_day:,.0f} ₽/сутки".replace(',', ' ')
        elif self.rental_term == 'long_term' and self.price_per_month:
            return f"{self.price_per_month:,.0f} ₽/месяц".replace(',', ' ')
        elif self.rental_term == 'both':
            prices = []
            if self.price_per_day:
                prices.append(f"{self.price_per_day:,.0f} ₽/сутки".replace(',', ' '))
            if self.price_per_month:
                prices.append(f"{self.price_per_month:,.0f} ₽/месяц".replace(',', ' '))
            return " / ".join(prices)
        return "Цена не указана"
    
    @property
    def location_display(self):
        """Красивое отображение локации"""
        if self.district:
            return f"{self.city.name}, {self.district.name}" # type: ignore
        elif self.city:
            return self.city.name
        return "Локация не указана"
    
    class Meta:
        verbose_name = 'Объект недвижимости'
        verbose_name_plural = 'Объекты недвижимости'
        ordering = ['-created_at']