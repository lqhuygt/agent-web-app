from django.conf import settings
from django.db import models
from django.db.models import Q


class Stock(models.Model):
    variant = models.OneToOneField('catalog.ProductVariant', on_delete=models.PROTECT, related_name='stock')
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        permissions = [('adjust_stock', 'Can adjust stock')]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=0), name='stock_quantity_nonnegative'),
            models.CheckConstraint(condition=Q(low_stock_threshold__gte=0), name='stock_threshold_nonnegative'),
        ]

    def __str__(self):
        return f'{self.variant.sku}: {self.quantity}'


class StockMovement(models.Model):
    variant = models.ForeignKey('catalog.ProductVariant', on_delete=models.PROTECT, related_name='stock_movements')
    delta = models.IntegerField()
    before = models.PositiveIntegerField()
    after = models.PositiveIntegerField()
    reason = models.CharField(max_length=255)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    order = models.ForeignKey('orders.Order', null=True, blank=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.CheckConstraint(condition=Q(after=models.F('before') + models.F('delta')), name='stock_movement_balanced')]
