import pytest
from unittest.mock import patch
from django.contrib.auth.models import Permission, User
from django.core.exceptions import PermissionDenied, ValidationError

from inventory.models import Stock, StockMovement
from orders.models import OrderStatus, OrderStatusHistory
from orders.services import transition_order
from tests.order_helpers import make_order


@pytest.fixture
def manager(db):
    user = User.objects.create_user('orders', password='test-pass', is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename='transition_order'))
    return user


@pytest.mark.django_db
def test_forward_transitions_record_actor_and_reason(manager):
    order, _ = make_order()
    for status in (OrderStatus.CONFIRMED, OrderStatus.SHIPPING, OrderStatus.COMPLETED):
        order = transition_order(order_id=order.pk, target_status=status, actor=manager, reason='Processed')
        assert order.status == status
    assert list(OrderStatusHistory.objects.filter(order=order).values_list('from_status', 'to_status')) == [
        (OrderStatus.PENDING, OrderStatus.CONFIRMED),
        (OrderStatus.CONFIRMED, OrderStatus.SHIPPING),
        (OrderStatus.SHIPPING, OrderStatus.COMPLETED),
    ]
    assert all(row.actor_id == manager.pk and row.reason == 'Processed' and row.created_at
               for row in OrderStatusHistory.objects.filter(order=order))


@pytest.mark.django_db
@pytest.mark.parametrize('start,target', [
    (OrderStatus.PENDING, OrderStatus.SHIPPING),
    (OrderStatus.CONFIRMED, OrderStatus.PENDING),
    (OrderStatus.SHIPPING, OrderStatus.CANCELLED),
    (OrderStatus.COMPLETED, OrderStatus.CANCELLED),
])
def test_invalid_transition_rejected_without_changes(manager, start, target):
    order, variant = make_order()
    if start != OrderStatus.PENDING:
        transition_order(order_id=order.pk, target_status=OrderStatus.CONFIRMED, actor=manager)
    if start in (OrderStatus.SHIPPING, OrderStatus.COMPLETED):
        transition_order(order_id=order.pk, target_status=OrderStatus.SHIPPING, actor=manager)
    if start == OrderStatus.COMPLETED:
        transition_order(order_id=order.pk, target_status=OrderStatus.COMPLETED, actor=manager)
    before = OrderStatusHistory.objects.filter(order=order).count()
    with pytest.raises(ValidationError):
        transition_order(order_id=order.pk, target_status=target, actor=manager)
    order.refresh_from_db()
    assert order.status == start
    assert OrderStatusHistory.objects.filter(order=order).count() == before
    assert Stock.objects.get(variant=variant).quantity == 3


@pytest.mark.django_db
def test_cancel_twice_restores_exactly_once(manager):
    order, variant = make_order()
    first = transition_order(order_id=order.pk, target_status=OrderStatus.CANCELLED, actor=manager, reason='Khách yêu cầu')
    second = transition_order(order_id=order.pk, target_status=OrderStatus.CANCELLED, actor=manager, reason='Retry')
    assert first.status == second.status == OrderStatus.CANCELLED
    assert Stock.objects.get(variant=variant).quantity == 5
    assert list(StockMovement.objects.filter(order=order).order_by('id').values_list('delta', flat=True)) == [-2, 2]
    assert OrderStatusHistory.objects.filter(order=order).count() == 1
    assert StockMovement.objects.get(order=order, delta=2).actor_id == manager.pk


@pytest.mark.django_db
def test_transition_requires_permission(manager):
    order, _ = make_order()
    stranger = User.objects.create_user('stranger', password='test-pass', is_staff=True)
    with pytest.raises(PermissionDenied):
        transition_order(order_id=order.pk, target_status=OrderStatus.CANCELLED, actor=stranger)
    assert OrderStatusHistory.objects.count() == 0


@pytest.mark.django_db
def test_cancel_from_confirmed_restores_stock(manager):
    order, variant = make_order()
    transition_order(order_id=order.pk, target_status=OrderStatus.CONFIRMED, actor=manager)
    transition_order(order_id=order.pk, target_status=OrderStatus.CANCELLED, actor=manager)
    assert Stock.objects.get(variant=variant).quantity == 5
    assert list(OrderStatusHistory.objects.filter(order=order).values_list('to_status', flat=True)) == [
        OrderStatus.CONFIRMED, OrderStatus.CANCELLED,
    ]


@pytest.mark.django_db
def test_cancellation_write_failure_rolls_back_stock_and_status(manager):
    order, variant = make_order()
    with patch('orders.services.StockMovement.objects.create', side_effect=RuntimeError('write failed')):
        with pytest.raises(RuntimeError):
            transition_order(order_id=order.pk, target_status=OrderStatus.CANCELLED, actor=manager)
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING
    assert Stock.objects.get(variant=variant).quantity == 3
    assert StockMovement.objects.filter(order=order).count() == 1
    assert OrderStatusHistory.objects.filter(order=order).count() == 0
