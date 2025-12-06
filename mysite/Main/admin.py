from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Product, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'quantity', 'is_active']
    list_editable = ['price', 'quantity', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'total_price', 'status_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'product__name']
    
    # ВСЕГДА только для чтения
    readonly_fields = ['total_price', 'created_at']
    
    # Actions ТОЛЬКО для НЕ отмененных заказов
    actions = [
        'mark_as_paid',
        'mark_as_shipped', 
        'mark_as_delivered',
        'mark_as_canceled'
    ]
    
    # --- Пользовательское отображение статуса ---
    def status_display(self, obj):
        """Красивое отображение статуса с цветом"""
        colors = {
            'NEW': 'blue',
            'PAID': 'green',
            'SHIPPED': 'orange',
            'DELIVERED': 'purple',
            'CANCELED': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    
    # --- ACTIONS ---
    
    def mark_as_paid(self, request, queryset):
        """Пометить как Оплачен - ТОЛЬКО НЕ отмененные"""
        # Фильтруем ТОЛЬКО НЕ отмененные заказы
        non_canceled = queryset.exclude(status='CANCELED')
        count = non_canceled.update(status='PAID')
        
        if count > 0:
            self.message_user(request, f"{count} заказов помечено как 'Оплачен'")
        
        # Показываем предупреждение, если были отмененные
        canceled_count = queryset.filter(status='CANCELED').count()
        if canceled_count > 0:
            messages.warning(
                request, 
                f"Пропущено {canceled_count} отмененных заказов. Отмененные заказы нельзя менять."
            )
    mark_as_paid.short_description = "✅ Оплачен"
    
    def mark_as_shipped(self, request, queryset):
        """Пометить как Отправлен - ТОЛЬКО НЕ отмененные"""
        non_canceled = queryset.exclude(status='CANCELED')
        count = non_canceled.update(status='SHIPPED')
        
        if count > 0:
            self.message_user(request, f"{count} заказов помечено как 'Отправлен'")
        
        canceled_count = queryset.filter(status='CANCELED').count()
        if canceled_count > 0:
            messages.warning(
                request, 
                f"Пропущено {canceled_count} отмененных заказов."
            )
    mark_as_shipped.short_description = "🚚 Отправлен"
    
    def mark_as_delivered(self, request, queryset):
        """Пометить как Доставлен - ТОЛЬКО НЕ отмененные"""
        non_canceled = queryset.exclude(status='CANCELED')
        count = non_canceled.update(status='DELIVERED')
        
        if count > 0:
            self.message_user(request, f"{count} заказов помечено как 'Доставлен'")
        
        canceled_count = queryset.filter(status='CANCELED').count()
        if canceled_count > 0:
            messages.warning(
                request, 
                f"Пропущено {canceled_count} отмененных заказов."
            )
    mark_as_delivered.short_description = "📦 Доставлен"
    
    def mark_as_canceled(self, request, queryset):
        """Отмена заказа - ТОЛЬКО НЕ отмененные"""
        non_canceled = queryset.exclude(status='CANCELED')
        updated_count = 0
        
        for order in non_canceled:
            # Возвращаем товар на склад
            order.product.quantity += order.quantity
            order.product.save()
            
            # Меняем статус
            order.status = 'CANCELED'
            order.save()
            updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f"{updated_count} заказов отменено. Товар возвращен на склад.")
        
        # Показываем предупреждение, если были уже отмененные
        already_canceled = queryset.filter(status='CANCELED').count()
        if already_canceled > 0:
            messages.warning(
                request, 
                f"Пропущено {already_canceled} уже отмененных заказов."
            )
    mark_as_canceled.short_description = "❌ Отменить (вернуть товар)"
    
    # --- ФОРМЫ И РЕДАКТИРОВАНИЕ ---
    
    def get_readonly_fields(self, request, obj=None):
        """Определяем, какие поля только для чтения"""
        base_readonly = ['total_price', 'created_at']
        
        if obj:  # Если редактируем существующий заказ
            if obj.status == 'CANCELED':
                # Если заказ ОТМЕНЕН - ВСЕ поля только для чтения
                return [field.name for field in obj._meta.fields] + ['status_display']
            else:
                # Если НЕ отменен - только базовые поля + статус можно менять через actions
                return base_readonly + ['user', 'product', 'quantity']
        else:  # При создании нового заказа
            return base_readonly + ['status']  # статус по умолчанию NEW
    
    def get_fields(self, request, obj=None):
        """Определяем порядок полей в форме"""
        if obj and obj.status == 'CANCELED':
            # Для отмененного заказа показываем статус как текст
            return [
                'status_display',  # вместо выпадающего списка
                'user',
                'product', 
                'quantity',
                'total_price',
                'created_at'
            ]
        elif obj:  # Редактирование не отмененного заказа
            return [
                'status',
                'user',
                'product', 
                'quantity',
                'total_price',
                'created_at'
            ]
        else:  # Создание нового заказа
            return [
                'user',
                'product',
                'quantity'
            ]
    
    def get_form(self, request, obj=None, **kwargs):
        """Настраиваем форму"""
        form = super().get_form(request, obj, **kwargs)
        
        # Если редактируем отмененный заказ - убираем все поля из формы
        if obj and obj.status == 'CANCELED':
            for field_name in form.base_fields:
                form.base_fields[field_name].disabled = True
        
        return form
    
    # --- СОХРАНЕНИЕ И УДАЛЕНИЕ ---
    
    def save_model(self, request, obj, form, change):
        """Сохранение заказа в админке"""
        # Если редактируем существующий отмененный заказ - запрещаем сохранение
        if change and obj.status == 'CANCELED':
            messages.error(request, "Невозможно изменить отмененный заказ!")
            return
        
        # При создании нового заказа
        if not change:
            obj.status = 'NEW'
            
            # Предупреждение о количестве
            if obj.quantity > obj.product.quantity:
                messages.warning(
                    request, 
                    f"Внимание: заказываете {obj.quantity} шт., а на складе только {obj.product.quantity} шт."
                )
        
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование отмененных заказов"""
        if obj and obj.status == 'CANCELED':
            return False
        return super().has_change_permission(request, obj)
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем сообщение для отмененных заказов"""
        if object_id:
            obj = self.get_object(request, object_id)
            if obj and obj.status == 'CANCELED':
                extra_context = extra_context or {}
                extra_context['readonly_message'] = "Этот заказ отменен. Редактирование запрещено."
        
        return super().changeform_view(request, object_id, form_url, extra_context)