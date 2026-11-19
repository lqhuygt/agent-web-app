import pytest
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from inventory.models import Stock
from orders.models import OrderStatus
from tests.order_helpers import make_order


@pytest.mark.django_db
def test_order_admin_transition_requires_permission(client):
    order, variant = make_order()
    staff = User.objects.create_user('staff', password='test-pass', is_staff=True)
    staff.user_permissions.add(Permission.objects.get(codename='view_order'))
    client.force_login(staff)
    url = reverse('admin:orders_order_transition', args=[order.pk])
    assert client.post(url, {'target_status': OrderStatus.CANCELLED, 'reason': 'Khách yêu cầu'}).status_code == 403
    staff.user_permissions.add(Permission.objects.get(codename='transition_order'))
    assert client.post(url, {'target_status': OrderStatus.CANCELLED, 'reason': 'Khách yêu cầu'}).status_code == 302
    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
    assert Stock.objects.get(variant=variant).quantity == 5


@pytest.mark.django_db
def test_order_admin_fields_are_read_only(client):
    order, variant = make_order()
    owner = User.objects.create_superuser('owner', 'owner@example.com', 'test-pass')
    client.force_login(owner)
    response = client.get(reverse('admin:orders_order_change', args=[order.pk]))
    assert response.status_code == 200
    for field in ('status', 'subtotal', 'shipping_fee', 'total', 'unit_price', 'line_total'):
        assert f'name="{field}"'.encode() not in response.content
    assert b'ORDER-TEST-M' in response.content
    response = client.post(reverse('admin:orders_order_change', args=[order.pk]), {
        'status': OrderStatus.CANCELLED, 'total': 1, '_save': 'Save',
    })
    assert response.status_code in (200, 403)
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING
    assert Stock.objects.get(variant=variant).quantity == 3


@pytest.mark.django_db
def test_setup_roles_is_idempotent_and_limited():
    call_command('setup_roles')
    call_command('setup_roles')
    assert Group.objects.filter(name__in=['Product manager', 'Inventory manager', 'Order manager']).count() == 3
    order_perms = set(Group.objects.get(name='Order manager').permissions.values_list('codename', flat=True))
    assert {'view_order', 'transition_order'} <= order_perms
    assert 'adjust_stock' not in order_perms


@pytest.mark.django_db
@override_settings(FORM_ADMIN_LOGIN_LIMIT=2, FORM_CHECKOUT_LIMIT=2, FORM_RATE_WINDOW_SECONDS=900)
def test_login_and_checkout_rate_limits_are_database_backed(client):
    url = reverse('admin:login')
    for _ in range(2):
        assert client.post(url, {'username': 'missing', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.1').status_code == 200
    assert client.post(url, {'username': 'missing', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.1').status_code == 429
    assert client.post(url, {'username': 'missing', 'password': 'wrong'}, REMOTE_ADDR='10.0.0.2').status_code == 200
    checkout = reverse('checkout')
    for _ in range(2):
        assert client.post(checkout, {}, REMOTE_ADDR='10.0.0.3').status_code == 400
    assert client.post(checkout, {}, REMOTE_ADDR='10.0.0.3').status_code == 429
    from core.models import RateLimitBucket
    assert RateLimitBucket.objects.count() == 3
