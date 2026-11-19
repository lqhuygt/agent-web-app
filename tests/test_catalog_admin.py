import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from catalog.models import Category, Product, ProductVariant
from inventory.models import Stock, StockMovement


@pytest.mark.django_db
def test_stock_admin_cannot_edit_quantity_directly(client):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='TEST-M')
    stock = Stock.objects.get(variant=variant)
    admin = User.objects.create_superuser('owner', 'owner@example.com', 'test-pass')
    client.force_login(admin)
    response = client.get(reverse('admin:inventory_stock_change', args=[stock.pk]))
    assert response.status_code == 200
    assert b'name="quantity"' not in response.content
    assert b'Adjust stock' in response.content


@pytest.mark.django_db
def test_stock_movement_admin_is_read_only(client):
    admin = User.objects.create_superuser('owner', 'owner@example.com', 'test-pass')
    client.force_login(admin)
    response = client.get(reverse('admin:inventory_stockmovement_add'))
    assert response.status_code in (403, 404)
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_low_stock_filter_shows_only_variants_at_or_below_threshold(client):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    low = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='LOW-M')
    high = ProductVariant.objects.create(product=product, color='Xanh', size='M', sku='HIGH-M')
    Stock.objects.filter(variant=low).update(quantity=2)
    Stock.objects.filter(variant=high).update(quantity=10)
    admin = User.objects.create_superuser('owner', 'owner@example.com', 'test-pass')
    client.force_login(admin)
    response = client.get(reverse('admin:inventory_stock_changelist'), {'low_stock': 'yes'})
    assert response.status_code == 200
    assert b'LOW-M' in response.content
    assert b'HIGH-M' not in response.content


@pytest.mark.django_db
def test_adjustment_admin_route_requires_permission_and_records_movement(client):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='TEST-M')
    stock = Stock.objects.get(variant=variant)
    url = reverse('admin:inventory_stock_adjust', args=[stock.pk])
    staff = User.objects.create_user('staff', password='test-pass', is_staff=True)
    client.force_login(staff)
    assert client.post(url, {'delta': 3, 'reason': 'Nhập thêm'}).status_code == 403
    staff.user_permissions.add(Permission.objects.get(codename='adjust_stock'))
    response = client.post(url, {'delta': 3, 'reason': 'Nhập thêm'})
    assert response.status_code == 302
    stock.refresh_from_db()
    assert stock.quantity == 3
    assert StockMovement.objects.get(variant=variant).actor == staff


@pytest.mark.django_db
def test_stock_threshold_can_be_changed_without_editing_quantity(client):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='TEST-M')
    stock = Stock.objects.get(variant=variant)
    admin = User.objects.create_superuser('owner', 'owner@example.com', 'test-pass')
    client.force_login(admin)
    response = client.post(reverse('admin:inventory_stock_change', args=[stock.pk]), {
        'low_stock_threshold': 2, 'quantity': 999, '_save': 'Save'
    })
    assert response.status_code == 302
    stock.refresh_from_db()
    assert (stock.quantity, stock.low_stock_threshold) == (0, 2)
