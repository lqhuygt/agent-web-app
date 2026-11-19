import pytest
from django.contrib.auth.models import Permission, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from catalog.models import Category, Product, ProductVariant
from inventory.models import Stock, StockMovement
from inventory.services import adjust_stock


@pytest.fixture
def variant(db):
    category = Category.objects.create(name='Quần', slug='quan')
    product = Product.objects.create(category=category, name='Quần âu', slug='quan-au', price=449000)
    return ProductVariant.objects.create(product=product, color='Đen', size='M', sku='TEST-M')


@pytest.fixture
def manager(db):
    user = User.objects.create_user('warehouse', password='test-pass')
    user.user_permissions.add(Permission.objects.get(codename='adjust_stock'))
    return user


def test_adjust_stock_records_before_after_and_actor(variant, manager):
    movement = adjust_stock(variant_id=variant.pk, delta=5, reason='Nhập kho', actor=manager)
    assert (movement.before, movement.after, movement.delta, movement.actor_id) == (0, 5, 5, manager.pk)
    assert Stock.objects.get(variant=variant).quantity == 5


def test_negative_adjustment_is_rejected_without_history(variant, manager):
    adjust_stock(variant_id=variant.pk, delta=5, reason='Nhập kho', actor=manager)
    with pytest.raises(ValidationError):
        adjust_stock(variant_id=variant.pk, delta=-6, reason='Xuất kho', actor=manager)
    assert Stock.objects.get(variant=variant).quantity == 5
    assert StockMovement.objects.filter(variant=variant).count() == 1


def test_adjustment_requires_permission_and_reason(variant, manager):
    stranger = User.objects.create_user('stranger', password='test-pass')
    with pytest.raises(PermissionDenied):
        adjust_stock(variant_id=variant.pk, delta=2, reason='Nhập kho', actor=stranger)
    with pytest.raises(ValidationError):
        adjust_stock(variant_id=variant.pk, delta=2, reason='   ', actor=manager)
    assert StockMovement.objects.count() == 0


def test_stock_and_threshold_cannot_be_negative_at_database(variant):
    stock = Stock.objects.get(variant=variant)
    stock.quantity = -1
    with pytest.raises(IntegrityError), transaction.atomic():
        stock.save(update_fields=['quantity'])
    stock.quantity = 0
    stock.low_stock_threshold = -1
    with pytest.raises(IntegrityError), transaction.atomic():
        stock.save(update_fields=['low_stock_threshold'])


def test_new_variant_has_zero_stock_ready_for_admin_adjustment(variant):
    stock = Stock.objects.get(variant=variant)
    assert stock.quantity == 0
