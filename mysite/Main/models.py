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
        return f"{self.name} (осталось: {self.quantity})"
    
    # Этот метод возвращает название категории товара с решёткой в начале, используя встроенный метод Django.
    def get_category_display_with_hash(self):
        """Получить категорию с #"""
        return f"#{self.get_category_display()}"
    
    # Этот метод проверяет, можно ли заказать товар, учитывая его активность и достаточность количества на складе.
    def can_be_ordered(self, requested_quantity=1):
        """Можно ли заказать товар в указанном количестве"""
        return self.is_active and self.quantity >= requested_quantity and requested_quantity > 0
    
    # Этот метод уменьшает количество товара, 
    # если его достаточно, и возвращает результат операции (True/False).
    def decrease_quantity(self, amount=1):
        """Уменьшить количество товара"""
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
            return True
        return False
    
    # Этот метод увеличивает количество товара на указанное значение и сохраняет изменения в базе данных.
    def increase_quantity(self, amount=1):
        """Увеличить количество товара"""
        self.quantity += amount
        self.save()
        return True
    
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('PAID', 'Оплачен'),
        ('SHIPPED', 'Отправлен'),
        ('DELIVERED', 'Доставлен'),
        ('CANCELED', 'Отменен'),
    ]
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Пользователь"
        )
    product = models.ForeignKey(
        'Product', 
        on_delete=models.PROTECT, 
        verbose_name="Товар"
        )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество", 
        default=1,
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='NEW', 
        verbose_name="Статус заказа"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата создания"
        )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая стоимость",
        default=0.00,
        editable=False
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