from django.contrib import admin
from .models import Product, Order # Импортируем твои модели

# Импортируем стандартную модель пользователя, чтобы связать ее
from django.contrib.auth.models import User 

# --- 1. Регистрация модели Product (Товары) ---
# Это самый простой способ регистрации:
admin.site.register(Product)

# --- 2. Регистрация модели Order (Заказы) ---
# Мы зарегистрируем ее чуть более красиво, используя ModelAdmin
# для настройки отображения.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке заказов (в таблице)
    list_display = (
        'id', 
        'user', 
        'product', 
        'status', 
        'created_at'
    )
    
    # Поля, по которым можно фильтровать список
    list_filter = (
        'status', 
        'created_at'
    )
    
    # Поля, по которым можно искать (например, по имени пользователя)
    search_fields = (
        'user__username', # Двойное подчеркивание (__) позволяет искать по связанной модели User
        'product__name'
    )
    
    # Поля, доступные только для чтения (нельзя изменить из админки)
    readonly_fields = (
        'created_at',
    )
