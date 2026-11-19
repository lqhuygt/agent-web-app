import pytest
from django.core.management import call_command

from catalog.models import Product, ProductVariant
from inventory.models import Stock


@pytest.mark.django_db
def test_seed_is_idempotent_and_preserves_shop_edits():
    call_command('seed_demo')
    product = Product.objects.get(slug='form-demo-trousers')
    assert ProductVariant.objects.filter(product=product).count() == 4
    assert set(ProductVariant.objects.filter(product=product).values_list('size', flat=True)) == {'M', 'L'}
    assert set(ProductVariant.objects.filter(product=product).values_list('color', flat=True)) == {'Đen', 'Xanh navy'}
    product.price = 500000
    product.save(update_fields=['price'])
    stock = Stock.objects.get(variant__sku='FORM-DEMO-BLK-M')
    stock.quantity = 3
    stock.save(update_fields=['quantity'])
    call_command('seed_demo')
    product.refresh_from_db()
    stock.refresh_from_db()
    assert product.price == 500000
    assert stock.quantity == 3
    assert Product.objects.filter(slug='form-demo-trousers').count() == 1
