from decimal import Decimal

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, Product
from .queries import search_products


def home(request):
    products = search_products(q='', category_slug=None, min_price=None, max_price=None, sort='newest')[:6]
    return render(request, 'storefront/home.html', {
        'products': products.prefetch_related('images'),
        'categories': Category.objects.filter(active=True).order_by('name'),
    })


def _parse_price(value):
    if value in (None, ''):
        return None
    value = value.strip()
    if not value.isascii() or not value.isdigit() or len(value) > 12:
        raise ValueError
    return Decimal(value)


def product_list(request):
    params = request.GET
    error = ''
    try:
        minimum = _parse_price(params.get('min_price'))
        maximum = _parse_price(params.get('max_price'))
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError
    except ValueError:
        minimum = maximum = None
        error = 'Giá không hợp lệ. Hãy nhập số không âm và khoảng giá đúng.'
    products = search_products(
        q=params.get('q', ''),
        category_slug=params.get('category') or None,
        min_price=minimum,
        max_price=maximum,
        sort=params.get('sort', 'newest'),
    ).prefetch_related('images')
    page_obj = Paginator(products, 24).get_page(params.get('page'))
    preserved = params.copy()
    preserved.pop('page', None)
    return render(request, 'products/list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.filter(active=True).order_by('name'),
        'query_string': preserved.urlencode(),
        'error': error,
        'filters': params,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(active=True, category__active=True).select_related('category').prefetch_related('images'),
        slug=slug,
    )
    variants = list(product.variants.select_related('stock').order_by('color', 'size'))
    for variant in variants:
        variant.can_buy = variant.active and variant.stock.quantity > 0
    return render(request, 'products/detail.html', {'product': product, 'variants': variants})
