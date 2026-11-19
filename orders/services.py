import base64
import hashlib
import hmac
import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F

from catalog.models import ProductVariant
from core.models import ShopSettings
from inventory.models import Stock, StockMovement

from .exceptions import CheckoutConflict, InsufficientStock
from .models import CheckoutAttempt, Order, OrderItem, OrderStatus, OrderStatusHistory


@dataclass(frozen=True)
class CartLine:
    variant_id: int
    quantity: int


@dataclass(frozen=True)
class CheckoutInput:
    name: str
    phone: str
    address: str
    note: str = ''

    def cleaned(self):
        if any(not isinstance(value, str) for value in (self.name, self.phone, self.address, self.note)):
            raise ValidationError('Thông tin nhận hàng không hợp lệ.')
        name, phone, address, note = (value.strip() for value in (self.name, self.phone, self.address, self.note))
        if not 2 <= len(name) <= 120:
            raise ValidationError('Tên người nhận phải có 2–120 ký tự.')
        if not re.fullmatch(r'\+?[0-9]{9,15}', phone):
            raise ValidationError('Số điện thoại không hợp lệ.')
        if not 8 <= len(address) <= 300:
            raise ValidationError('Địa chỉ phải có 8–300 ký tự.')
        if len(note) > 500:
            raise ValidationError('Ghi chú quá dài.')
        return CheckoutInput(name, phone, address, note)


def tracking_token_for_attempt(session_key, idempotency_key):
    message = f'FORM order tracking:{session_key}:{idempotency_key}'.encode()
    raw = hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def token_hash(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def _fingerprint(customer, lines):
    payload = {'customer': asdict(customer), 'lines': [asdict(line) for line in lines]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


@transaction.atomic
def place_order(*, session_key: str, idempotency_key: UUID, customer: CheckoutInput,
                lines: list[CartLine]) -> Order:
    if not session_key or len(session_key) > 64 or not isinstance(idempotency_key, UUID):
        raise ValidationError('Yêu cầu đặt hàng không hợp lệ.')
    customer = customer.cleaned()
    if not lines or any(type(line.quantity) is not int or line.quantity < 1 or line.quantity > 10 for line in lines):
        raise ValidationError('Giỏ hàng không hợp lệ.')
    if len({line.variant_id for line in lines}) != len(lines):
        raise ValidationError('Giỏ hàng có biến thể trùng.')
    lines = sorted(lines, key=lambda line: line.variant_id)
    fingerprint = _fingerprint(customer, lines)
    attempt, _ = CheckoutAttempt.objects.get_or_create(
        session_key=session_key, idempotency_key=idempotency_key, defaults={'fingerprint': fingerprint}
    )
    attempt = CheckoutAttempt.objects.select_for_update().get(pk=attempt.pk)
    if attempt.fingerprint != fingerprint:
        raise CheckoutConflict('Checkout key reused with different content.')
    token = tracking_token_for_attempt(session_key, idempotency_key)
    if attempt.order_id:
        order = attempt.order
        order._tracking_token = token
        return order

    locked = []
    subtotal = Decimal('0')
    for line in lines:
        try:
            stock = Stock.objects.select_for_update().get(variant_id=line.variant_id)
            variant = ProductVariant.objects.select_for_update().select_related('product__category').get(pk=line.variant_id)
        except (Stock.DoesNotExist, ProductVariant.DoesNotExist):
            raise InsufficientStock('Sản phẩm không còn bán.') from None
        if not (variant.active and variant.product.active and variant.product.category.active):
            raise InsufficientStock('Sản phẩm không còn bán.')
        if stock.quantity < line.quantity:
            raise InsufficientStock('Không đủ hàng trong kho.')
        price = variant.product.price
        subtotal += price * line.quantity
        locked.append((line, variant, stock, price))

    shop, _ = ShopSettings.objects.get_or_create(pk=1)
    shipping_fee = Decimal('0') if subtotal >= shop.free_shipping_threshold else shop.flat_shipping_fee
    order = Order.objects.create(
        customer_name=customer.name, customer_phone=customer.phone,
        shipping_address=customer.address, note=customer.note,
        subtotal=subtotal, shipping_fee=shipping_fee, total=subtotal + shipping_fee,
        tracking_token_hash=token_hash(token),
    )
    order.display_number = f'FORM-{order.pk:06d}'
    order.save(update_fields=['display_number'])
    for line, variant, stock, price in locked:
        OrderItem.objects.create(
            order=order, variant=variant, quantity=line.quantity,
            snapshot_name=variant.product.name, snapshot_sku=variant.sku,
            snapshot_color=variant.color, snapshot_size=variant.size,
            unit_price=price, line_total=price * line.quantity,
        )
        before = stock.quantity
        changed = Stock.objects.filter(pk=stock.pk, quantity__gte=line.quantity).update(quantity=F('quantity') - line.quantity)
        if changed != 1:
            raise InsufficientStock('Không đủ hàng trong kho.')
        StockMovement.objects.create(
            variant=variant, delta=-line.quantity, before=before, after=before - line.quantity,
            reason='Đặt hàng COD', actor=None, order=order,
        )
    attempt.order = order
    attempt.save(update_fields=['order'])
    order._tracking_token = token
    return order


ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
    OrderStatus.CONFIRMED: (OrderStatus.SHIPPING, OrderStatus.CANCELLED),
    OrderStatus.SHIPPING: (OrderStatus.COMPLETED,),
    OrderStatus.COMPLETED: (),
    OrderStatus.CANCELLED: (),
}


@transaction.atomic
def transition_order(*, order_id: int, target_status: OrderStatus, actor, reason: str = '') -> Order:
    if not actor or not actor.is_authenticated or not actor.has_perm('orders.transition_order'):
        raise PermissionDenied('Order transition permission required.')
    if not isinstance(reason, str) or len(reason.strip()) > 255:
        raise ValidationError('Lý do không hợp lệ hoặc quá dài.')
    reason = reason.strip()
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status == target_status == OrderStatus.CANCELLED:
        return order
    if target_status not in ALLOWED_TRANSITIONS.get(order.status, ()):
        raise ValidationError('Không thể chuyển sang trạng thái này.')
    if target_status == OrderStatus.CANCELLED:
        for item in order.items.order_by('variant_id', 'id'):
            stock = Stock.objects.select_for_update().get(variant_id=item.variant_id)
            before = stock.quantity
            stock.quantity = before + item.quantity
            stock.save(update_fields=['quantity'])
            StockMovement.objects.create(
                variant_id=item.variant_id, delta=item.quantity, before=before,
                after=stock.quantity, reason=reason or 'Hủy đơn hàng', actor=actor, order=order,
            )
    previous = order.status
    order.status = target_status
    order.save(update_fields=['status'])
    OrderStatusHistory.objects.create(
        order=order, from_status=previous, to_status=target_status, actor=actor, reason=reason,
    )
    return order
