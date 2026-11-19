from django.db import models
from django.db.models import Q


class ShopSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    flat_shipping_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    free_shipping_threshold = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    class Meta:
        verbose_name = 'Shop settings'
        verbose_name_plural = 'Shop settings'
        constraints = [
            models.CheckConstraint(condition=Q(id=1), name='shop_settings_singleton'),
            models.CheckConstraint(condition=Q(flat_shipping_fee__gte=0), name='shop_fee_nonnegative'),
            models.CheckConstraint(condition=Q(free_shipping_threshold__gte=0), name='shop_threshold_nonnegative'),
        ]

    def __str__(self):
        return 'Shop settings'


class RateLimitBucket(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    window_started_at = models.DateTimeField()
