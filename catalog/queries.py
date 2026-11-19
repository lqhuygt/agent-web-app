from decimal import Decimal

from .models import Product, normalize_search_text


SORT_OPTIONS = {
    'newest': ('-id',),
    'price_asc': ('price', 'id'),
    'price_desc': ('-price', 'id'),
    'name': ('search_name', 'id'),
}


def search_products(*, q: str, category_slug: str | None, min_price: Decimal | None,
                    max_price: Decimal | None, sort: str):
    products = Product.objects.filter(active=True, category__active=True).select_related('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)
    for term in normalize_search_text(q).split():
        products = products.filter(search_name__contains=term)
    return products.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS['newest']))
