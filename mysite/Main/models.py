# Main/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

# models.py - добавляем поле description
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('MONO', 'моно_букеты'), 
        ('MIXED', 'сборные_букеты'), 
        ('GIFT', 'подарочные_наборы'), 
        ('COMP', 'композиции'), 
        ('WEDDING', 'свадебные_букеты'), 
        ('BUSINESS', 'деловые_букеты')
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Категория", null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True, null=True)  # ← ДОБАВЛЕНО
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Склад")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/', verbose_name="Изображение", null=True, blank=True)
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
    
    def __str__(self):
        return f"{self.id}. {self.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('PAID', 'Оплачен'),
        ('SHIPPED', 'Отправлен'),
        ('DELIVERED', 'Доставлен'),
        ('CANCELED', 'Отменен'),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        verbose_name="Товар",
        related_name='orders'
    )
    quantity = models.PositiveIntegerField("Количество", default=1, validators=[MinValueValidator(1)])
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='NEW')
    total_price = models.DecimalField("Общая стоимость", max_digits=10, decimal_places=2, default=0.00, editable=False)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        verbose_name="Пользователь",
        null=True, 
        blank=True
    )
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ №{self.id} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Вычисляем общую стоимость
        if self.product:
            self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)