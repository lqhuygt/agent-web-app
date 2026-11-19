from decimal import Decimal

import pytest

from catalog.models import Category, Product
from catalog.queries import search_products


@pytest.mark.django_db
@pytest.mark.parametrize('query', ['quan au', 'QUẦN ÂU', '  quần   âu  '])
def test_search_matches_accents_case_and_extra_spaces(query):
    category = Category.objects.create(name='Quần', slug='quan')
    target = Product.objects.create(category=category, name='Quần Âu Slim', slug='quan-au', price=Decimal('449000'))
    assert list(search_products(q=query, category_slug=None, min_price=None, max_price=None, sort='newest')) == [target]


@pytest.mark.django_db
def test_search_index_updates_when_name_changes():
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần Âu', slug='quan-au', price=Decimal('449000'))
    product.name = 'Áo Polo'
    product.save(update_fields=['name'])
    assert product in search_products(q='ao polo', category_slug=None, min_price=None, max_price=None, sort='newest')
    assert product not in search_products(q='quan au', category_slug=None, min_price=None, max_price=None, sort='newest')


@pytest.mark.django_db
def test_combined_filters_sort_and_hidden_products():
    pants = Category.objects.create(name='Quần', slug='quan')
    shirts = Category.objects.create(name='Áo', slug='ao')
    cheap = Product.objects.create(category=pants, name='Quần âu rẻ', slug='cheap', price=Decimal('400000'))
    expected = Product.objects.create(category=pants, name='Quần âu đẹp', slug='expected', price=Decimal('500000'))
    Product.objects.create(category=pants, name='Quần âu đắt', slug='expensive', price=Decimal('700000'))
    Product.objects.create(category=shirts, name='Quần âu khác', slug='other', price=Decimal('500000'))
    Product.objects.create(category=pants, name='Quần âu ẩn', slug='hidden', price=Decimal('500000'), active=False)
    assert list(search_products(q='quan au', category_slug='quan', min_price=Decimal('450000'), max_price=Decimal('600000'), sort='price_asc')) == [expected]
    pants.active = False
    pants.save(update_fields=['active'])
    assert cheap not in search_products(q='quan au', category_slug=None, min_price=None, max_price=None, sort='newest')


@pytest.mark.django_db
def test_unsupported_sort_is_ignored():
    category = Category.objects.create(name='Quần', slug='quan')
    Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=Decimal('449000'))
    assert search_products(q='', category_slug=None, min_price=None, max_price=None, sort='price;DROP TABLE').count() == 1
