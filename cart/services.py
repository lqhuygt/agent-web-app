from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from catalog.models import ProductVariant


CART_SESSION_KEY = 'cart'
MAX_QUANTITY = 10


@dataclass
class CartEntry:
    variant: ProductVariant
    quantity: int
    available: bool
    line_total: Decimal


def set_cart_quantity(*, request, variant_id: int, quantity: int) -> None:
    if type(quantity) is not int or quantity < 0 or quantity > MAX_QUANTITY:
        raise ValidationError('Số lượng phải từ 0 đến 10.')
    key = str(variant_id)
    cart = request.session.get(CART_SESSION_KEY, {}).copy()
    if quantity == 0:
        cart.pop(key, None)
    else:
        try:
            variant = ProductVariant.objects.select_related('product__category', 'stock').get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            raise ValidationError('Biến thể không tồn tại.') from None
        if not (variant.active and variant.product.active and variant.product.category.active):
            raise ValidationError('Sản phẩm hiện không bán.')
        if quantity > variant.stock.quantity:
            raise ValidationError('Không đủ hàng trong kho.')
        cart[key] = quantity
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def get_cart_entries(request):
    raw = request.session.get(CART_SESSION_KEY, {})
    ids = [int(key) for key in raw if str(key).isdigit()]
    variants = ProductVariant.objects.filter(pk__in=ids).select_related('product__category', 'stock')
    by_id = {str(variant.pk): variant for variant in variants}
    entries = []
    total = Decimal('0')
    for key, quantity in raw.items():
        variant = by_id.get(key)
        if not variant or type(quantity) is not int or quantity < 1:
            continue
        available = (
            variant.active and variant.product.active and variant.product.category.active
            and variant.stock.quantity >= quantity
        )
        line_total = variant.product.price * quantity
        total += line_total
        entries.append(CartEntry(variant, quantity, available, line_total))
    return entries, total
