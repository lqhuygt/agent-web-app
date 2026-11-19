from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission, User
from django.db import connections

from inventory.models import Stock, StockMovement
from orders.models import OrderStatus, OrderStatusHistory
from orders.services import transition_order
from tests.order_helpers import make_order


@pytest.mark.django_db(transaction=True)
def test_concurrent_cancellation_restores_once():
    order, variant = make_order()
    manager = User.objects.create_user('orders', password='test-pass', is_staff=True)
    manager.user_permissions.add(Permission.objects.get(codename='transition_order'))
    barrier = Barrier(2)

    def cancel():
        try:
            barrier.wait(timeout=10)
            return transition_order(order_id=order.pk, target_status=OrderStatus.CANCELLED, actor=manager).status
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(cancel)
        second = pool.submit(cancel)
        assert first.result(timeout=20) == second.result(timeout=20) == OrderStatus.CANCELLED
    assert Stock.objects.get(variant=variant).quantity == 5
    assert list(StockMovement.objects.filter(order=order).order_by('id').values_list('delta', flat=True)) == [-2, 2]
    assert OrderStatusHistory.objects.filter(order=order).count() == 1
