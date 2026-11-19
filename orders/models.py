from django.db import models
from django.db.models import Q


class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Chờ xác nhận'
    CONFIRMED = 'CONFIRMED', 'Đã xác nhận'
    SHIPPING = 'SHIPPING', 'Đang giao'
    COMPLETED = 'COMPLETED', 'Hoàn tất'
    CANCELLED = 'CANCELLED', 'Đã hủy'


class Order(models.Model):
    display_number = models.CharField(max_length=32, unique=True, null=True, blank=True)
    status = models.CharField(max_length=12, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=16)
    shipping_address = models.CharField(max_length=300)
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=0)
    total = models.DecimalField(max_digits=12, decimal_places=0)
    tracking_token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.CheckConstraint(condition=Q(subtotal__gte=0), name='order_subtotal_nonnegative'),
            models.CheckConstraint(condition=Q(shipping_fee__gte=0), name='order_shipping_nonnegative'),
            models.CheckConstraint(condition=Q(total=models.F('subtotal') + models.F('shipping_fee')), name='order_total_balanced'),
        ]

    @property
    def tracking_token(self):
        return getattr(self, '_tracking_token', None)

    def __str__(self):
        return self.display_number or f'Order {self.pk}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    variant = models.ForeignKey('catalog.ProductVariant', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    snapshot_name = models.CharField(max_length=200)
    snapshot_sku = models.CharField(max_length=80)
    snapshot_color = models.CharField(max_length=80)
    snapshot_size = models.CharField(max_length=40)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=1), name='order_item_quantity_positive'),
            models.CheckConstraint(condition=Q(line_total=models.F('unit_price') * models.F('quantity')), name='order_item_total_balanced'),
        ]


class CheckoutAttempt(models.Model):
    session_key = models.CharField(max_length=64)
    idempotency_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['session_key', 'idempotency_key'], name='unique_checkout_per_session')]
