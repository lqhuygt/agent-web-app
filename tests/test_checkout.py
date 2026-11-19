from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from catalog.models import Category, Product, ProductVariant
from core.models import ShopSettings
from inventory.models import Stock, StockMovement
from orders.exceptions import CheckoutConflict, InsufficientStock
from orders.models import CheckoutAttempt, Order, OrderItem, OrderStatus
from orders.services import CartLine, CheckoutInput, place_order


@pytest.fixture
def variant(db):
    ShopSettings.objects.create(flat_shipping_fee=Decimal('30000'), free_shipping_threshold=Decimal('699000'))
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=Decimal('449000'))
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='PANTS-BLK-M')
    Stock.objects.filter(variant=variant).update(quantity=5)
    return variant


def customer(**changes):
    values = {'name': 'Nguyễn Văn An', 'phone': '0912345678', 'address': '12 Nguyễn Huệ, Quận 1, TP HCM', 'note': ''}
    values.update(changes)
    return CheckoutInput(**values)


def test_order_total_stock_and_snapshot(variant):
    order = place_order(session_key='buyer-a', idempotency_key=uuid4(), customer=customer(), lines=[CartLine(variant.pk, 1)])
    assert (order.subtotal, order.shipping_fee, order.total) == (Decimal('449000'), Decimal('30000'), Decimal('479000'))
    assert order.status == OrderStatus.PENDING
    assert Stock.objects.get(variant=variant).quantity == 4
    item = order.items.get()
    assert (item.snapshot_name, item.snapshot_sku, item.unit_price, item.line_total) == ('Quần âu', 'PANTS-BLK-M', Decimal('449000'), Decimal('449000'))
    assert StockMovement.objects.get(order=order.pk).delta == -1
    variant.product.price = Decimal('500000')
    variant.product.name = 'Tên mới'
    variant.product.save(update_fields=['price', 'name'])
    item.refresh_from_db()
    assert (item.snapshot_name, item.unit_price) == ('Quần âu', Decimal('449000'))


def test_free_shipping_at_threshold(variant):
    order = place_order(session_key='buyer-b', idempotency_key=uuid4(), customer=customer(), lines=[CartLine(variant.pk, 2)])
    assert (order.subtotal, order.shipping_fee, order.total) == (Decimal('898000'), Decimal('0'), Decimal('898000'))


def test_same_key_same_payload_returns_same_order_and_different_payload_conflicts(variant):
    key = uuid4()
    first = place_order(session_key='buyer-c', idempotency_key=key, customer=customer(), lines=[CartLine(variant.pk, 1)])
    again = place_order(session_key='buyer-c', idempotency_key=key, customer=customer(), lines=[CartLine(variant.pk, 1)])
    assert again.pk == first.pk
    assert Order.objects.count() == 1
    assert Stock.objects.get(variant=variant).quantity == 4
    with pytest.raises(CheckoutConflict):
        place_order(session_key='buyer-c', idempotency_key=key, customer=customer(note='Changed'), lines=[CartLine(variant.pk, 1)])
    assert StockMovement.objects.count() == 1


def test_failure_saving_item_rolls_back_order_stock_history_and_attempt(variant):
    with patch('orders.services.OrderItem.objects.create', side_effect=RuntimeError('write failed')):
        with pytest.raises(RuntimeError):
            place_order(session_key='buyer-d', idempotency_key=uuid4(), customer=customer(), lines=[CartLine(variant.pk, 1)])
    assert (Order.objects.count(), OrderItem.objects.count(), StockMovement.objects.count(), CheckoutAttempt.objects.count()) == (0, 0, 0, 0)
    assert Stock.objects.get(variant=variant).quantity == 5


def test_server_rejects_invalid_customer_and_insufficient_stock(variant):
    with pytest.raises(ValidationError):
        place_order(session_key='buyer-e', idempotency_key=uuid4(), customer=customer(phone='x'), lines=[CartLine(variant.pk, 1)])
    with pytest.raises(ValidationError):
        place_order(session_key='buyer-e', idempotency_key=uuid4(), customer=customer(name=None), lines=[CartLine(variant.pk, 1)])
    with pytest.raises(InsufficientStock):
        place_order(session_key='buyer-e', idempotency_key=uuid4(), customer=customer(), lines=[CartLine(variant.pk, 6)])
    assert Order.objects.count() == 0
