from decimal import Decimal

import pytest
from django.urls import reverse
from django.contrib.staticfiles import finders

from catalog.models import Category, Product, ProductVariant
from inventory.models import Stock


@pytest.mark.django_db
def test_home_and_product_list_show_active_products(client):
    category = Category.objects.create(name='Quần', slug='quan')
    Product.objects.create(category=category, name='Quần âu FORM', slug='quan-au', price=Decimal('449000'))
    Product.objects.create(category=category, name='Quần ẩn', slug='hidden', price=Decimal('449000'), active=False)
    assert b'FORM' in client.get('/').content
    response = client.get('/products/')
    assert response.status_code == 200
    assert 'Quần âu FORM' in response.content.decode()
    assert 'Quần ẩn' not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize('bad_price', ['abc', '-1', '1.5', '1e1000'])
def test_filter_errors_are_visible_and_not_server_errors(client, bad_price):
    response = client.get('/products/', {'min_price': bad_price})
    assert response.status_code == 200
    assert 'Giá không hợp lệ' in response.content.decode()


@pytest.mark.django_db
def test_pagination_preserves_search_query(client):
    category = Category.objects.create(name='Quần', slug='quan')
    for index in range(25):
        Product.objects.create(category=category, name=f'Quần âu {index}', slug=f'quan-au-{index}', price=Decimal('449000'))
    response = client.get('/products/', {'q': 'quan au'})
    assert response.status_code == 200
    assert len(response.context['page_obj']) == 24
    assert 'q=quan+au' in response.content.decode()


@pytest.mark.django_db
def test_detail_shows_variants_and_stock_status(client):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu FORM', slug='quan-au', price=Decimal('449000'))
    available = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='BLACK-M')
    empty = ProductVariant.objects.create(product=product, color='Xanh', size='L', sku='BLUE-L')
    Stock.objects.filter(variant=available).update(quantity=3)
    response = client.get(reverse('product_detail', args=[product.slug]))
    body = response.content.decode()
    assert response.status_code == 200
    assert 'Đen / M' in body and 'Xanh / L' in body
    assert 'Hết hàng' in body
    assert 'BLACK-M' in body
    assert Stock.objects.get(variant=empty).quantity == 0


@pytest.mark.django_db
def test_hidden_product_detail_returns_404(client):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Ẩn', slug='hidden', price=Decimal('449000'), active=False)
    assert client.get(reverse('product_detail', args=[product.slug])).status_code == 404


def test_storefront_assets_are_served_by_django_staticfiles():
    assert finders.find('css/storefront.css')
    assert finders.find('js/htmx.min.js')
