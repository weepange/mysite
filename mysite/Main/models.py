from django.db import models
from django.contrib.auth.models import User # Импортируем стандартную модель пользователя

# --- 1. Модель Товаров (Product) ---
class Product(models.Model):
    # ID товара создается автоматически
    
    CATEGORY_CHOICES = [
        ('MONO', '#моно_букеты'),
        ('MIXED', '#сборные_букеты'),
        ('GIFT', '#подарочные_наборы'),
        ('COMP', '#композиции'),
        ('WEDDING', '#свадебные_букеты'),
        ('BUSINESS', '#деловые_букеты'),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория товара",
        help_text="Выберите тип букета",
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=255, 
        verbose_name="Название товара"
        )
    
    description = models.TextField(
        verbose_name="Описание товара"
        )


    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    # Используем ImageField для хранения пути к картинке
    # Для работы с файлами и картинками тебе может понадобиться установить pillow: pip install Pillow
    image = models.ImageField(
        upload_to='products/', 
        blank=True, 
        null=True, 
        verbose_name="Картинка товара"
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        #Без них модель в админке будет называться просто "Product" (или "Твое_Приложение | Product"). 
        # С ними она будет называться "Товар" в единственном числе и "Товары" во множественном числе, что гораздо удобнее для русскоязычного пользователя и администратора.

    #Чтобы присваивалось значение которое отправляется с форм
    def __str__(self):
        return self.name
    

    def get_category_display_with_hash(self):
        """Получить категорию с #"""
        return f"#{self.get_category_display()}"

# --- 2. Модель Заказов (Order) ---
class Order(models.Model):
    # ID заказа создается автоматически
    
    # СВЯЗЬ 1: Заказ связан с Пользователем (ForeignKey)
    # Один пользователь может иметь много заказов.
    # on_delete=models.CASCADE означает, что при удалении пользователя, удалятся и все его заказы.
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Пользователь"
    )

    # СВЯЗЬ 2: Заказ связан с Товаром (ForeignKey)
    # Один товар может быть во многих заказах (в нашей упрощенной схеме).
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, # PROTECT не даст удалить товар, пока он есть в заказе.
        verbose_name="Товар"
    )
    
    STATUS_CHOICES = [
        ('NOPAID', 'Неоплачен'),
        ('PAID', 'Оплачен'),
        ('SHIPPED', 'Отправлен'),
        ('DELIVERED', 'Доставлен'),
        ('CANCELED', 'Отменен'),
    ]

    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='NEW',
        verbose_name="Статус заказа"
    )
    
    # Поле для времени создания заказа
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        # Сортируем заказы по дате создания
        ordering = ['-created_at']
        
    #Чтобы присваивалось значение которое отправляется с форм
    def __str__(self):
        return f"Заказ №{self.id} от {self.user.username} - Статус: {self.status}"
        #Ну и тут просто удобство представления данных
