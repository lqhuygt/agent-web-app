from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import OrderTransitionForm
from .models import Order, OrderItem, OrderStatusHistory
from .services import ALLOWED_TRANSITIONS, transition_order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ('snapshot_name', 'snapshot_sku', 'snapshot_color', 'snapshot_size',
              'quantity', 'unit_price', 'line_total')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('orders.view_order')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('display_number', 'status', 'created_at', 'total', 'transition_link')
    list_filter = ('status', 'created_at')
    search_fields = ('display_number', 'customer_name', 'customer_phone', 'items__snapshot_sku')
    readonly_fields = ('display_number', 'status', 'customer_name', 'customer_phone',
                       'shipping_address', 'note', 'subtotal', 'shipping_fee', 'total',
                       'created_at', 'transition_link')
    fields = ('display_number', 'status', 'transition_link', 'customer_name', 'customer_phone',
              'shipping_address', 'note', 'subtotal', 'shipping_fee', 'total', 'created_at')
    inlines = (OrderItemInline,)
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def transition_link(self, obj):
        if not obj or obj.pk is None or not ALLOWED_TRANSITIONS.get(obj.status):
            return ''
        return format_html('<a href="{}">Chuyển trạng thái</a>',
                           reverse('admin:orders_order_transition', args=[obj.pk]))
    transition_link.short_description = 'Xử lý'

    def get_urls(self):
        custom = [path('<path:object_id>/transition/', self.admin_site.admin_view(self.transition_view),
                       name='orders_order_transition')]
        return custom + super().get_urls()

    def transition_view(self, request, object_id):
        if not request.user.has_perm('orders.transition_order'):
            return HttpResponseForbidden()
        order = get_object_or_404(Order, pk=object_id)
        form = OrderTransitionForm(request.POST or None, order=order)
        if request.method == 'POST' and form.is_valid():
            try:
                transition_order(
                    order_id=order.pk, target_status=form.cleaned_data['target_status'],
                    actor=request.user, reason=form.cleaned_data['reason'],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                self.message_user(request, 'Đã cập nhật trạng thái đơn.', messages.SUCCESS)
                return redirect('admin:orders_order_change', order.pk)
        context = {
            **self.admin_site.each_context(request), 'title': f'Xử lý {order.display_number}',
            'order': order, 'form': form, 'opts': self.model._meta,
        }
        return render(request, 'admin/orders/transition.html', context)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'from_status', 'to_status', 'actor', 'reason', 'created_at')
    list_filter = ('to_status', 'created_at')
    search_fields = ('order__display_number',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
