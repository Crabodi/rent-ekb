from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    """
    Расширенная модель пользователя для сервиса аренды
    """
    ROLE_CHOICES = [
        ('tenant', 'Арендатор'),
        ('landlord', 'Арендодатель'),
        ('both', 'И арендатор, и арендодатель'),
    ]
    
    # Переопределяем email, делаем его уникальным и обязательным
    email = models.EmailField(
        'Email адрес',
        unique=True,
        help_text='Обязательное поле. Используется для входа и уведомлений'
    )
    
    # Телефон с валидацией формата
    phone_regex = RegexValidator(
        regex=r'^\+?7?\d{10,15}$',
        message="Телефон должен быть в формате: '+7XXXXXXXXXX'"
    )
    phone = models.CharField(
        'Телефон', 
        max_length=20, 
        unique=True,
        validators=[phone_regex],
        help_text='Номер телефона в формате +7XXXXXXXXXX'
    )
    
    role = models.CharField(
        'Роль', 
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='both'
    )
    
    avatar = models.ImageField(
        'Аватар', 
        upload_to='avatars/%Y/%m/', 
        null=True, 
        blank=True
    )
    
    telegram_id = models.CharField(
        'Telegram ID', 
        max_length=100, 
        blank=True, 
        null=True
    )
    
    bio = models.TextField('О себе', max_length=500, blank=True)
    
    # Флаг согласия на рассылку
    email_notifications = models.BooleanField(
        'Получать уведомления на email',
        default=True
    )
    
    # Верификация email
    email_verified = models.BooleanField(
        'Email подтвержден',
        default=False
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']