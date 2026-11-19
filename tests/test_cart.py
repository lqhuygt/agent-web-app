from decimal import Decimal

import pytest
from django.test import Client

from cart.services import set_cart_quantity
from catalog.models import Category, Product, ProductVariant
from inventory.models import Stock


@pytest.fixture
def variant(db):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=Decimal('449000'))
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='BLACK-M')
    Stock.objects.filter(variant=variant).update(quantity=5)
    return variant


def test_cart_sessions_are_independent(variant):
    first, second = Client(), Client()
    assert first.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 2}).status_code == 302
    assert '898.000' in first.get('/cart/').content.decode()
    assert '898.000' not in second.get('/cart/').content.decode()


def test_cart_uses_current_server_price(variant):
    client = Client()
    client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 2})
    variant.product.price = Decimal('500000')
    variant.product.save(update_fields=['price'])
    assert '1.000.000' in client.get('/cart/').content.decode()


def test_add_rejects_more_than_stock_or_ten_units(variant):
    client = Client()
    assert client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 6}).status_code == 400
    Stock.objects.filter(variant=variant).update(quantity=20)
    assert client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 11}).status_code == 400
    assert 'BLACK-M' not in client.get('/cart/').content.decode()


@pytest.mark.parametrize('quantity', ['-1', 'abc', '1.5'])
def test_update_rejects_invalid_quantities(variant, quantity):
    client = Client()
    client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1})
    assert client.post('/cart/update/', {'variant_id': variant.pk, 'quantity': quantity}).status_code == 400
    assert '449.000' in client.get('/cart/').content.decode()


def test_update_zero_removes_variant(variant):
    client = Client()
    client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1})
    assert client.post('/cart/update/', {'variant_id': variant.pk, 'quantity': 0}).status_code == 302
    assert 'Giỏ hàng trống' in client.get('/cart/').content.decode()


def test_hidden_or_out_of_stock_variant_is_rejected(variant):
    client = Client()
    Stock.objects.filter(variant=variant).update(quantity=0)
    assert client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1}).status_code == 400
    Stock.objects.filter(variant=variant).update(quantity=5)
    variant.active = False
    variant.save(update_fields=['active'])
    assert client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1}).status_code == 400


def test_cart_post_requires_csrf(variant):
    client = Client(enforce_csrf_checks=True)
    assert client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1}).status_code == 403


def test_hx_cart_update_returns_fragment(variant):
    client = Client()
    response = client.post('/cart/add/', {'variant_id': variant.pk, 'quantity': 1}, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert b'id="cart-region"' in response.content
