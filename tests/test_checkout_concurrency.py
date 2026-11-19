from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from django.db import connections

from catalog.models import Category, Product, ProductVariant
from core.models import ShopSettings
from inventory.models import Stock, StockMovement
from orders.exceptions import InsufficientStock
from orders.models import Order
from orders.services import CartLine, CheckoutInput, place_order


@pytest.fixture
def variant(transactional_db):
    ShopSettings.objects.create(flat_shipping_fee=30000, free_shipping_threshold=699000)
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='LAST-ONE')
    Stock.objects.filter(variant=variant).update(quantity=1)
    return variant


def run_race(variant, *, same_key):
    barrier = Barrier(2)
    key = uuid4()
    customer = CheckoutInput('Nguyễn Văn An', '0912345678', '12 Nguyễn Huệ, Quận 1, TP HCM', '')

    def buy(index):
        try:
            barrier.wait(timeout=10)
            order = place_order(
                session_key='same-buyer' if same_key else f'buyer-{index}',
                idempotency_key=key if same_key else uuid4(),
                customer=customer,
                lines=[CartLine(variant.pk, 1)],
            )
            return order.pk
        except InsufficientStock:
            return 'sold-out'
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(buy, 1)
        second = pool.submit(buy, 2)
        return first.result(timeout=20), second.result(timeout=20)


def test_last_unit_two_sessions_only_one_order(variant):
    results = run_race(variant, same_key=False)
    assert sorted(str(value) for value in results).count('sold-out') == 1
    assert Order.objects.count() == 1
    assert Stock.objects.get(variant=variant).quantity == 0
    assert StockMovement.objects.filter(variant=variant).count() == 1


def test_same_key_concurrently_returns_one_order_and_one_decrement(variant):
    results = run_race(variant, same_key=True)
    assert results[0] == results[1]
    assert Order.objects.count() == 1
    assert Stock.objects.get(variant=variant).quantity == 0
    assert StockMovement.objects.filter(variant=variant).count() == 1
