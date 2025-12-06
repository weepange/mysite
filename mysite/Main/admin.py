from django.contrib import admin
from .models import Product, Order
# Импортируем стандартную модель пользователя, чтобы связать ее
from django.contrib.auth.models import User 
from django.contrib import admin
from .models import Product, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    #Эта строка определяет, какие поля товара будут отображаться в списке товаров в админке Django.
    list_display = ['name', 'category', 'price', 'quantity', 'is_active']

    #Эта строка позволяет редактировать поля количества, 
    #активности и цены прямо из списка товаров в админке Django.
    list_editable = ['quantity', 'is_active', 'price']
    #фильтр товаров(Слева)
    list_filter = ['category', 'is_active']
    #Эти строки добавляют поиск по названию и описанию товаров в админке
    # и подключают кастомные действия для массовой активации/деактивации.
    search_fields = ['name', 'description']
    actions = ['make_active', 'make_inactive']
    
    #Эта функция массово активирует выбранные товары через админку, устанавливая им is_active=True
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Активировать выбранные товары"
    
    #Эта функция в Django-админке массово деактивирует выбранные товары, устанавливая им is_active=False
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Деактивировать выбранные товары"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    #Эта строка определяет, какие поля заказа будут отображаться в списке заказов в админке Django.
    list_display = ['id', 'user', 'product', 'quantity', 'total_price', 'status', 'created_at']

    #Фильтрация слева
    list_filter = ['status', 'created_at']
    #Это добавляет поиск в админке по имени пользователя и названию товара в списке заказов.

    search_fields = ['user__username', 'product__name']
    #Эта строка делает поля total_price и created_at доступными только для чтения 
    # в форме редактирования заказа в админке Django.
    readonly_fields = ['total_price', 'created_at']

    #Эта строка добавляет в админку действие для массовой отмены выбранных заказов через выпадающий список.
    actions = ['cancel_orders']
    
    #Эта функция массово отменяет выбранные заказы через админку
    # вызывая метод update_status('CANCELED') для каждого еще не отмененного заказа.
    def cancel_orders(self, request, queryset):
        for order in queryset:
            if order.status != 'CANCELED':
                order.update_status('CANCELED')
    cancel_orders.short_description = "Отменить выбранные заказы"
