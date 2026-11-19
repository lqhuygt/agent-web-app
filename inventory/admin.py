from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import F
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import StockAdjustmentForm
from .models import Stock, StockMovement
from .services import adjust_stock


class LowStockFilter(admin.SimpleListFilter):
    title = 'low stock'
    parameter_name = 'low_stock'

    def lookups(self, request, model_admin):
        return [('yes', 'At or below threshold')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(quantity__lte=F('low_stock_threshold'))
        return queryset


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('variant', 'quantity', 'low_stock_threshold', 'adjust_link')
    readonly_fields = ('variant', 'quantity', 'adjust_link')
    fields = ('variant', 'quantity', 'low_stock_threshold', 'adjust_link')
    search_fields = ('variant__sku', 'variant__product__name')
    list_filter = (LowStockFilter,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return super().has_view_permission(request, obj) or request.user.has_perm('inventory.adjust_stock')

    def adjust_link(self, obj):
        if not obj or not obj.pk:
            return ''
        url = reverse('admin:inventory_stock_adjust', args=[obj.pk])
        return format_html('<a href="{}">Adjust stock</a>', url)

    def get_urls(self):
        custom = [path('<path:object_id>/adjust/', self.admin_site.admin_view(self.adjust_view), name='inventory_stock_adjust')]
        return custom + super().get_urls()

    def adjust_view(self, request, object_id):
        if not request.user.has_perm('inventory.adjust_stock'):
            return HttpResponseForbidden()
        stock = get_object_or_404(Stock.objects.select_related('variant'), pk=object_id)
        form = StockAdjustmentForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            try:
                adjust_stock(
                    variant_id=stock.variant_id,
                    delta=form.cleaned_data['delta'],
                    reason=form.cleaned_data['reason'],
                    actor=request.user,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                self.message_user(request, 'Stock adjusted.', messages.SUCCESS)
                return redirect('admin:inventory_stock_changelist')
        context = {
            **self.admin_site.each_context(request),
            'title': 'Adjust stock',
            'stock': stock,
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/inventory/adjust_stock.html', context)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('variant', 'delta', 'before', 'after', 'reason', 'actor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('variant__sku', 'reason')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
