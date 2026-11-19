from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product, ProductVariant
from core.models import ShopSettings
from inventory.models import Stock, StockMovement


class Command(BaseCommand):
    help = 'Create deterministic demo catalog data without overwriting shop edits.'

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='form-demo-pants', defaults={'name': 'Quần nam mẫu'}
        )
        product, _ = Product.objects.get_or_create(
            slug='form-demo-trousers',
            defaults={
                'category': category,
                'name': 'Quần âu FORM mẫu',
                'description': 'Dữ liệu mẫu để thử giao diện và quản lý kho.',
                'price': Decimal('449000'),
                'size_guide': 'M, L',
            },
        )
        for color, code in [('Đen', 'BLK'), ('Xanh navy', 'NVY')]:
            for size in ('M', 'L'):
                variant, variant_created = ProductVariant.objects.get_or_create(
                    sku=f'FORM-DEMO-{code}-{size}',
                    defaults={'product': product, 'color': color, 'size': size},
                )
                stock, _ = Stock.objects.get_or_create(variant=variant)
                if variant_created:
                    stock.quantity = 8
                    stock.save(update_fields=['quantity'])
                    StockMovement.objects.create(
                        variant=variant, delta=8, before=0, after=8,
                        reason='Khởi tạo dữ liệu mẫu', actor=None,
                    )
        ShopSettings.objects.get_or_create(
            pk=1,
            defaults={'flat_shipping_fee': Decimal('30000'), 'free_shipping_threshold': Decimal('699000')},
        )
        self.stdout.write(self.style.SUCCESS('Demo catalog is ready.'))
