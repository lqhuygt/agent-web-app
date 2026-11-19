import logging
from uuid import uuid4

import pytest
from django.test import Client

from catalog.models import Category, Product, ProductVariant
from core.models import ShopSettings
from inventory.models import Stock
from orders.models import Order
from orders.services import CartLine, CheckoutInput, place_order
from core.logging import RedactOrderTokens


@pytest.fixture
def variant(db):
    ShopSettings.objects.create(flat_shipping_fee=30000, free_shipping_threshold=699000)
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='PANTS-BLK-M')
    Stock.objects.filter(variant=variant).update(quantity=5)
    return variant


def test_tracking_requires_secret_token_and_escapes_customer_content(client, variant):
    customer = CheckoutInput('Nguyễn <script>alert(1)</script>', '0912345678', '12 Nguyễn Huệ, Quận 1, TP HCM', '<script>alert(2)</script>')
    order = place_order(session_key='buyer-one', idempotency_key=uuid4(), customer=customer, lines=[CartLine(variant.pk, 1)])
    token = order.tracking_token
    assert len(token) >= 43
    assert token not in order.tracking_token_hash
    assert client.get('/orders/track/invalid-token/').status_code == 404
    assert client.get(f'/orders/{order.pk}/').status_code == 404
    response = client.get(f'/orders/track/{token}/')
    body = response.content.decode()
    assert response.status_code == 200
    assert response['Referrer-Policy'] == 'no-referrer'
    assert '&lt;script&gt;' in body and '<script>alert' not in body
    assert 'https://' not in body
    assert 'Không chia sẻ liên kết' in body


def test_guest_checkout_ignores_client_price_clears_cart_and_retries_safely(variant):
    client = Client()
    client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1})
    checkout = client.get('/checkout/')
    assert checkout.status_code == 200
    key = checkout.context['idempotency_key']
    payload = {'idempotency_key': key, 'name': 'Nguyễn Văn An', 'phone': '0912345678', 'address': '12 Nguyễn Huệ, Quận 1, TP HCM', 'note': '', 'total': '1'}
    first = client.post('/checkout/', payload)
    assert first.status_code == 302
    order = Order.objects.get()
    assert order.total == 479000
    assert client.session.get('cart') == {}
    second = client.post('/checkout/', payload)
    assert second.status_code == 302 and second['Location'] == first['Location']
    assert Order.objects.count() == 1
    changed = client.post('/checkout/', {**payload, 'note': 'Different'})
    assert changed.status_code == 409


def test_checkout_post_requires_csrf(variant):
    client = Client(enforce_csrf_checks=True)
    assert client.post('/checkout/', {'name': 'Test'}).status_code == 403


def test_tracking_token_is_redacted_from_access_log():
    token = 'A' * 43
    record = logging.LogRecord('django.server', logging.INFO, '', 0, 'GET /orders/track/%s/ HTTP/1.1', (token,), None)
    RedactOrderTokens().filter(record)
    assert token not in record.getMessage()
    assert '/orders/track/[redacted]/' in record.getMessage()
