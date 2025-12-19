# admin.py - исправленный с полем описания
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone
from .models import Product, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview', 'name', 'category_display', 'price', 'quantity', 'is_active', 'updated_at_display')
    list_display_links = ('id', 'name')
    list_editable = ('price', 'quantity', 'is_active')
    search_fields = ('name', 'category', 'description')
    list_filter = ('category', 'is_active')
    readonly_fields = ('image_preview_large', 'updated_at_display_field')
    
    # Сворачиваемое поле для описания
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'category', 'description', 'price', 'quantity', 'is_active')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview_large')
        }),
        ('Дополнительно', {
            'fields': ('updated_at_display_field',),
            'classes': ('collapse',)
        }),
    )
    
    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Категория'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "📷 Нет"
    image_preview.short_description = 'Изображение'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; border-radius: 4px;" />', obj.image.url)
        return "Нет изображения"
    image_preview_large.short_description = 'Предпросмотр'
    
    def updated_at_display(self, obj):
        if obj.updated_at:
            moscow_time = timezone.localtime(obj.updated_at)
            return moscow_time.strftime('%d.%m.%Y %H:%M')
        return "-"
    updated_at_display.short_description = 'Обновлено'
    
    def updated_at_display_field(self, obj):
        return self.updated_at_display(obj)
    updated_at_display_field.short_description = 'Обновлено'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_info', 'product_info', 'quantity', 'total_price_display', 'status_display', 'created_at_display')
    list_display_links = ('id',)
    list_filter = ('status', 'created_at', 'product')
    search_fields = ('id', 'user__username', 'product__name', 'product__description')
    readonly_fields = ('product_link', 'user', 'quantity', 'total_price', 'status_display_field', 'created_at_display_field')
    
    # Разрешаем создание и просмотр, но запрещаем редактирование статуса вручную
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # При редактировании существующего заказа
            return ('product', 'user', 'quantity', 'total_price', 'status', 'created_at', 'status_display_field', 'created_at_display_field')
        else:    # При создании нового заказа
            return ('total_price', 'status')
    
    def get_fields(self, request, obj=None):
        if obj:  # При редактировании существующего заказа
            return ('product', 'user', 'quantity', 'total_price', 'status_display_field', 'created_at_display_field')
        else:    # При создании нового заказа
            return ('product', 'user', 'quantity')
    
    def get_fieldsets(self, request, obj=None):
        if obj:  # При редактировании существующего заказа
            return (
                ('Информация о заказе', {
                    'fields': ('product', 'user', 'quantity', 'total_price')
                }),
                ('Статус и даты', {
                    'fields': ('status_display_field', 'created_at_display_field')
                }),
            )
        else:    # При создании нового заказа
            return (
                ('Создание нового заказа', {
                    'fields': ('product', 'user', 'quantity'),
                    'description': 'При создании заказа товар будет зарезервирован на складе'
                }),
            )
    
    actions = ['mark_as_paid_action', 'mark_as_shipped_action', 'mark_as_delivered_action', 'cancel_order_action']
    
    def save_model(self, request, obj, form, change):
        try:
            with transaction.atomic():
                if not change:  # Новый заказ
                    if obj.quantity > obj.product.quantity:
                        raise ValidationError(
                            f"❌ Недостаточно товара '{obj.product.name}' на складе. "
                            f"Доступно: {obj.product.quantity}, требуется: {obj.quantity}"
                        )
                    
                    obj.product.quantity -= obj.quantity
                    obj.product.save()
                    obj.total_price = obj.product.price * obj.quantity
                    obj.status = 'NEW'
                    
                    messages.success(
                        request, 
                        f"✅ Заказ создан успешно! Товар '{obj.product.name}' зарезервирован. "
                        f"Остаток на складе: {obj.product.quantity}"
                    )
                else:
                    messages.info(request, "ℹ️ Изменения сохранены. Для изменения статуса используйте Actions.")
                
                super().save_model(request, obj, form, change)
                
        except ValidationError as e:
            messages.error(request, str(e))
            raise
        except Exception as e:
            messages.error(request, f"❌ Ошибка: {str(e)}")
            raise
    
    def delete_model(self, request, obj):
        try:
            with transaction.atomic():
                if obj.status != 'CANCELED':
                    obj.product.quantity += obj.quantity
                    obj.product.save()
                    messages.success(
                        request,
                        f"✅ Товар '{obj.product.name}' возвращен на склад. "
                        f"Новый остаток: {obj.product.quantity}"
                    )
                super().delete_model(request, obj)
        except Exception as e:
            messages.error(request, f"❌ Ошибка при удалении: {str(e)}")
            raise
    
    def delete_queryset(self, request, queryset):
        try:
            with transaction.atomic():
                for order in queryset:
                    if order.status != 'CANCELED':
                        order.product.quantity += order.quantity
                        order.product.save()
                super().delete_queryset(request, queryset)
                messages.success(request, f"✅ Удалено {queryset.count()} заказов. Товар возвращен на склад.")
        except Exception as e:
            messages.error(request, f"❌ Ошибка при удалении: {str(e)}")
            raise
    
    # Отображение полей в админке
    def user_info(self, obj):
        if obj.user:
            return obj.user.username
        return "👤 Гость"
    user_info.short_description = 'Пользователь'
    
    def product_info(self, obj):
        # Добавляем краткое описание при наведении
        description_preview = ""
        if obj.product.description:
            # Обрезаем описание для отображения в таблице
            if len(obj.product.description) > 50:
                description_preview = obj.product.description[:47] + "..."
            else:
                description_preview = obj.product.description
            
            return format_html(
                '<strong>#{}</strong>. <a href="{}" title="{}">{}</a>', 
                obj.product.id,
                reverse('admin:Main_product_change', args=[obj.product.id]), 
                obj.product.description,
                obj.product.name
            )
        else:
            return format_html(
                '<strong>#{}</strong>. <a href="{}">{}</a>', 
                obj.product.id,
                reverse('admin:Main_product_change', args=[obj.product.id]), 
                obj.product.name
            )
    product_info.short_description = 'Товар'
    
    def total_price_display(self, obj):
        return f"{obj.total_price:.2f} ₽"
    total_price_display.short_description = 'Сумма'
    
    def status_display(self, obj):
        icons = {
            'NEW': '🆕',
            'PAID': '💰', 
            'SHIPPED': '🚚',
            'DELIVERED': '✅',
            'CANCELED': '❌'
        }
        colors = {
            'NEW': '#3498db',
            'PAID': '#f39c12',
            'SHIPPED': '#9b59b6',
            'DELIVERED': '#27ae60',
            'CANCELED': '#e74c3c'
        }
        icon = icons.get(obj.status, '')
        color = colors.get(obj.status, '#000')
        status_text = obj.get_status_display()
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 3px 8px; border-radius: 3px; background-color: {}20;">{} {}</span>', 
            color, color, icon, status_text
        )
    status_display.short_description = "Статус"
    
    def status_display_field(self, obj):
        return self.status_display(obj)
    status_display_field.short_description = "Статус"
    
    def created_at_display(self, obj):
        if obj.created_at:
            moscow_time = timezone.localtime(obj.created_at)
            return moscow_time.strftime('%d.%m.%Y %H:%M')
        return "-"
    created_at_display.short_description = 'Дата создания'
    
    def created_at_display_field(self, obj):
        return self.created_at_display(obj)
    created_at_display_field.short_description = 'Дата создания'
    
    def product_link(self, obj):
        # Показываем описание при наведении на ссылку
        if obj.product.description:
            return format_html(
                '<a href="{}" title="{}"><strong>#{}</strong>. {}</a>', 
                reverse('admin:Main_product_change', args=[obj.product.id]),
                obj.product.description,
                obj.product.id,
                obj.product.name
            )
        else:
            return format_html(
                '<a href="{}"><strong>#{}</strong>. {}</a>', 
                reverse('admin:Main_product_change', args=[obj.product.id]),
                obj.product.id,
                obj.product.name
            )
    product_link.short_description = 'Товар'
    
    # Actions для массового изменения статусов
    @admin.action(description="💰 Пометить как оплаченные")
    def mark_as_paid_action(self, request, queryset):
        success = 0
        failed = 0
        errors = []
        
        for order in queryset:
            try:
                with transaction.atomic():
                    if order.status == 'NEW':
                        if order.quantity > order.product.quantity:
                            errors.append(f"Заказ №{order.id}: недостаточно товара '{order.product.name}' на складе. Доступно: {order.product.quantity}, требуется: {order.quantity}")
                            failed += 1
                            continue
                        
                        order.status = 'PAID'
                        order.save(update_fields=['status'])
                        success += 1
                    else:
                        errors.append(f"Заказ №{order.id}: можно оплачивать только новые заказы")
                        failed += 1
            except Exception as e:
                errors.append(f"Заказ №{order.id}: ошибка - {str(e)}")
                failed += 1
        
        if success:
            self.message_user(request, f"✅ Оплачено заказов: {success}")
        if failed:
            error_message = f"❌ Не удалось оплатить: {failed} заказов"
            if errors:
                error_message += f": {', '.join(errors[:5])}"
            self.message_user(request, error_message, level=messages.WARNING)
    
    @admin.action(description="🚚 Пометить как отправленные")
    def mark_as_shipped_action(self, request, queryset):
        success = 0
        failed = 0
        errors = []
        
        for order in queryset:
            try:
                with transaction.atomic():
                    if order.status == 'PAID':
                        order.status = 'SHIPPED'
                        order.save(update_fields=['status'])
                        success += 1
                    else:
                        errors.append(f"Заказ №{order.id}: можно отправлять только оплаченные заказы")
                        failed += 1
            except Exception as e:
                errors.append(f"Заказ №{order.id}: ошибка - {str(e)}")
                failed += 1
        
        if success:
            self.message_user(request, f"✅ Отправлено заказов: {success}")
        if failed:
            error_message = f"❌ Не удалось отправить: {failed} заказов"
            if errors:
                error_message += f": {', '.join(errors[:5])}"
            self.message_user(request, error_message, level=messages.WARNING)
    
    @admin.action(description="✅ Пометить как доставленные")
    def mark_as_delivered_action(self, request, queryset):
        success = 0
        failed = 0
        errors = []
        
        for order in queryset:
            try:
                with transaction.atomic():
                    if order.status == 'SHIPPED':
                        order.status = 'DELIVERED'
                        order.save(update_fields=['status'])
                        success += 1
                    else:
                        errors.append(f"Заказ №{order.id}: можно доставлять только отправленные заказы")
                        failed += 1
            except Exception as e:
                errors.append(f"Заказ №{order.id}: ошибка - {str(e)}")
                failed += 1
        
        if success:
            self.message_user(request, f"✅ Доставлено заказов: {success}")
        if failed:
            error_message = f"❌ Не удалось доставить: {failed} заказов"
            if errors:
                error_message += f": {', '.join(errors[:5])}"
            self.message_user(request, error_message, level=messages.WARNING)
    
    @admin.action(description="❌ Отменить заказы (вернуть товар)")
    def cancel_order_action(self, request, queryset):
        success = 0
        failed = 0
        errors = []
        
        for order in queryset:
            try:
                with transaction.atomic():
                    if order.status not in ['DELIVERED', 'CANCELED']:
                        order.product.quantity += order.quantity
                        order.product.save()
                        order.status = 'CANCELED'
                        order.save(update_fields=['status'])
                        success += 1
                    else:
                        errors.append(f"Заказ №{order.id}: нельзя отменить доставленные или уже отмененные заказы")
                        failed += 1
            except Exception as e:
                errors.append(f"Заказ №{order.id}: ошибка - {str(e)}")
                failed += 1
        
        if success:
            self.message_user(
                request, 
                f"✅ Отменено заказов: {success}. Товар возвращен на склад."
            )
        if failed:
            error_message = f"❌ Не удалось отменить: {failed} заказов"
            if errors:
                error_message += f": {', '.join(errors[:5])}"
            self.message_user(request, error_message, level=messages.WARNING)