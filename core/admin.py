from django.contrib import admin

from .models import ShopSettings


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('flat_shipping_fee', 'free_shipping_threshold')

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not ShopSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
