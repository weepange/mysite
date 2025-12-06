from django.db import models
from django.contrib.auth.models import User # Импортируем стандартную модель пользователя
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

class Product(models.Model):
    #Указанные теги для фильтрации товаров
    CATEGORY_CHOICES = [
        ('MONO', '#моно_букеты'),
        ('MIXED', '#сборные_букеты'),
        ('GIFT', '#подарочные_наборы'),
        ('COMP', '#композиции'),
        ('WEDDING', '#свадебные_букеты'),
        ('BUSINESS', '#деловые_букеты'),
    ]

    #Разделение по категориям, чтобы в дальшейшем было удобно их фильтровать
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория товара",
        help_text="Выберите тип букета",
        null=True,
        blank=True
    )

    #Название товара
    name = models.CharField(
        max_length=255, 
        verbose_name="Название товара"
    )

    #Описание товара
    description = models.TextField(
        verbose_name="Описание товара"
    )

    #Цена товара
    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    #Поле количества товара на складе
    quantity = models.PositiveIntegerField(
        verbose_name="Количество на складе",
        default=0,
        help_text="Доступное количество товара"
    )

    #Подгрузка картинок самого товара
    image = models.ImageField(
        upload_to='products/', 
        blank=True, 
        null=True, 
        verbose_name="Картинка товара"
    )

    #Поле активности товара
    is_active = models.BooleanField(
        verbose_name="Активный товар",
        default=True,
        help_text="Отображается ли товар в каталоге"
    )

    #Для удобного отображения в Админке
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    #Возврат значений в более удобной форме
    def __str__(self):
        return f"{self.name} (осталось: {self.quantity})"
    
    #Этот метод возвращает название категории товара с решёткой в начале, используя встроенный метод Django.
    def get_category_display_with_hash(self):
        """Получить категорию с #"""
        return f"#{self.get_category_display()}"
    
    #Этот метод проверяет, можно ли заказать товар, учитывая его активность и достаточность количества на складе.
    def can_be_ordered(self, requested_quantity=1):
        """Можно ли заказать товар в указанном количестве"""
        return self.is_active and self.quantity >= requested_quantity and requested_quantity > 0
    
    #Этот метод уменьшает количество товара, 
    # если его достаточно, и возвращает результат операции (True/False).
    def decrease_quantity(self, amount=1):
        """Уменьшить количество товара"""
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
            return True
        return False
    
    #Этот метод увеличивает количество товара на указанное значение и сохраняет изменения в базе данных.
    def increase_quantity(self, amount=1):
        """Увеличить количество товара"""
        self.quantity += amount
        self.save()
        return True
    
class Order(models.Model):
    #Теги для статуса заказа
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('NOPAID', 'Неоплачен'),
        ('PAID', 'Оплачен'),
        ('SHIPPED', 'Отправлен'),
        ('DELIVERED', 'Доставлен'),
        ('CANCELED', 'Отменен'),
    ]
    #Заказ закрепляется за пользователем
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        #Если пользователь (User) удаляется из базы данных 
        #Все заказы (Order), которые были связаны с этим пользователем
        # Автоматически удаляются из базы данных
        verbose_name="Пользователь"
    )

    #Защита заказа если кто-то задумает удалить товар
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,# собственно здесь защита от удаления
        verbose_name="Товар"
    )
    
    #количество товара в заказе
    quantity = models.PositiveIntegerField(
        verbose_name="Количество",
        default=1,
        validators=[MinValueValidator(1)]#минимальное значение которое возможно
    )
    #статус заказа
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, #принимает значения их списка тэгов
        default='NEW',
        verbose_name="Статус заказа"
    )
    #Время создания заказа в точности
    created_at = models.DateTimeField(auto_now_add=True)
    
    #общая стоимость для упрощения логики и понимания 
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая стоимость",
        default=0.00,
        editable=False  # не редактируется вручную
    )

    #Также для удобства представления в Админке
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
        
    #Удобство представления заказа
    def __str__(self):
        return f"Заказ №{self.id} - {self.product.name} x{self.quantity}"

    #Этот метод проверяет перед сохранением заказа, 
    #достаточно ли товара на складе для указанного количества, и выбрасывает ошибку при недостатке.
    def clean(self):
        """Валидация перед сохранением"""
        if not self.product.can_be_ordered(self.quantity):
            raise ValidationError(
                f"Недостаточно товара '{self.product.name}'. "
                f"Доступно: {self.product.quantity}, запрошено: {self.quantity}"
            )

    #Этот метод автоматически вычисляет общую стоимость заказа
    # и при создании нового заказа проверяет доступность товара и уменьшает его количество на складе.
    def save(self, *args, **kwargs):
        # Вычисляем общую стоимость(цена * количество)
        self.total_price = self.product.price * self.quantity
        
        # Если это новый заказ (не отмененный)
        if not self.pk and self.status != 'CANCELED':
            # Проверяем доступность
            if not self.product.can_be_ordered(self.quantity):
                raise ValidationError(
                    f"Недостаточно товара '{self.product.name}'"
                )
            # Уменьшаем количество
            self.product.decrease_quantity(self.quantity)
        
        super().save(*args, **kwargs)
    
    #Этот метод безопасно обновляет статус заказа, 
    #автоматически возвращая товар на склад при отмене и проверяя доступность при восстановлении заказа.
    def update_status(self, new_status):
        """Метод для изменения статуса с проверкой"""
        old_status = self.status
        
        # Если меняем на "Отменен" и заказ не был отменен
        if new_status == 'CANCELED' and old_status != 'CANCELED':
            # Возвращаем товар на склад
            self.product.increase_quantity(self.quantity)
        
        # Если отмена отменяется (статус меняется с CANCELED на другой)
        elif old_status == 'CANCELED' and new_status != 'CANCELED':
            # Проверяем доступность
            if not self.product.can_be_ordered(self.quantity):
                raise ValidationError(
                    f"Недостаточно товара для восстановления заказа"
                )
            # Снова уменьшаем количество
            self.product.decrease_quantity(self.quantity)
        self.status = new_status
        self.save()