from uuid import uuid4

from catalog.models import Category, Product, ProductVariant
from inventory.models import Stock
from orders.services import CartLine, CheckoutInput, place_order


def make_order(*, quantity=2, stock_quantity=5):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    variant = ProductVariant.objects.create(product=product, color='Đen', size='M', sku='ORDER-TEST-M')
    Stock.objects.filter(variant=variant).update(quantity=stock_quantity)
    order = place_order(
        session_key='order-test', idempotency_key=uuid4(),
        customer=CheckoutInput('Nguyễn Văn An', '0912345678', '12 Nguyễn Huệ, Quận 1, TP HCM'),
        lines=[CartLine(variant.pk, quantity)],
    )
    return order, variant
