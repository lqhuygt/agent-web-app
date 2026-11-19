from decimal import Decimal
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from PIL import Image

from catalog.models import Category, Product, ProductImage, ProductVariant
from core.models import ShopSettings


@pytest.fixture
def product(db):
    category = Category.objects.create(name='Quần', slug='quan')
    return Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=Decimal('449000'))


def test_variant_sku_and_combination_are_unique(product):
    ProductVariant.objects.create(product=product, color='Đen', size='M', sku='FORM-PANTS-BLK-M')
    with pytest.raises(IntegrityError), transaction.atomic():
        ProductVariant.objects.create(product=product, color='Xanh', size='M', sku='FORM-PANTS-BLK-M')
    with pytest.raises(IntegrityError), transaction.atomic():
        ProductVariant.objects.create(product=product, color='Đen', size='M', sku='OTHER')


def test_negative_price_is_rejected_by_database(product):
    product.price = Decimal('-1')
    with pytest.raises(IntegrityError), transaction.atomic():
        product.save(update_fields=['price'])


def test_shop_settings_are_singleton_and_nonnegative(db):
    settings = ShopSettings.objects.create(flat_shipping_fee=Decimal('30000'), free_shipping_threshold=Decimal('699000'))
    assert settings.pk == 1
    with pytest.raises(IntegrityError), transaction.atomic():
        ShopSettings.objects.create(flat_shipping_fee=Decimal('1'))
    settings.flat_shipping_fee = Decimal('-1')
    with pytest.raises(IntegrityError), transaction.atomic():
        settings.save(update_fields=['flat_shipping_fee'])


def test_product_image_rejects_svg_and_oversized_files(product):
    svg = SimpleUploadedFile('bad.svg', b'<svg xmlns="http://www.w3.org/2000/svg"/>', content_type='image/svg+xml')
    with pytest.raises(ValidationError):
        ProductImage(product=product, image=svg).full_clean()
    huge = SimpleUploadedFile('huge.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png')
    with pytest.raises(ValidationError):
        ProductImage(product=product, image=huge).full_clean()


def test_product_image_rejects_invalid_content(product):
    fake = SimpleUploadedFile('fake.png', b'not a png', content_type='image/png')
    with pytest.raises(ValidationError):
        ProductImage(product=product, image=fake).full_clean()


def test_product_image_accepts_real_png(product):
    buffer = BytesIO()
    Image.new('RGB', (1, 1), 'red').save(buffer, format='PNG')
    upload = SimpleUploadedFile('real.png', buffer.getvalue(), content_type='image/png')
    ProductImage(product=product, image=upload).full_clean()
