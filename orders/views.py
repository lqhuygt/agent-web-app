import re
from uuid import UUID, uuid4

from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.debug import sensitive_post_parameters

from cart.services import CART_SESSION_KEY, get_cart_entries

from .exceptions import CheckoutConflict, InsufficientStock
from .forms import CheckoutForm
from .models import CheckoutAttempt, Order
from .services import CartLine, CheckoutInput, place_order, token_hash, tracking_token_for_attempt


def _lines_from_cart(raw):
    return [CartLine(int(variant_id), quantity) for variant_id, quantity in raw.items()]


@sensitive_post_parameters('name', 'phone', 'address', 'note')
def checkout(request):
    entries, total = get_cart_entries(request)
    if request.method == 'GET':
        if entries and not request.session.get('checkout_key'):
            request.session['checkout_key'] = str(uuid4())
        form = CheckoutForm(initial={'idempotency_key': request.session.get('checkout_key', '')})
        return render(request, 'checkout/page.html', {
            'form': form, 'entries': entries, 'total': total,
            'idempotency_key': request.session.get('checkout_key'),
        })
    if request.method != 'POST':
        raise Http404
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(request, 'checkout/page.html', {'form': form, 'entries': entries, 'total': total}, status=400)
    key = form.cleaned_data['idempotency_key']
    last = request.session.get('last_checkout')
    active_key = request.session.get('checkout_key')
    if str(key) == active_key:
        raw_lines = request.session.get(CART_SESSION_KEY, {})
    elif last and str(key) == last['key']:
        raw_lines = request.session.get(CART_SESSION_KEY, {}) or last['lines']
    else:
        form.add_error(None, 'Yêu cầu đặt hàng đã hết hạn. Vui lòng tải lại trang.')
        return render(request, 'checkout/page.html', {'form': form, 'entries': entries, 'total': total}, status=409)
    customer = CheckoutInput(
        name=form.cleaned_data['name'], phone=form.cleaned_data['phone'],
        address=form.cleaned_data['address'], note=form.cleaned_data['note'],
    )
    try:
        lines = _lines_from_cart(raw_lines)
        order = place_order(
            session_key=request.session.session_key,
            idempotency_key=key, customer=customer, lines=lines,
        )
    except CheckoutConflict:
        form.add_error(None, 'Yêu cầu này đã được dùng với thông tin khác.')
        return render(request, 'checkout/page.html', {'form': form, 'entries': entries, 'total': total}, status=409)
    except (ValidationError, InsufficientStock) as exc:
        form.add_error(None, exc)
        return render(request, 'checkout/page.html', {'form': form, 'entries': entries, 'total': total}, status=400)
    request.session['last_checkout'] = {'key': str(key), 'lines': raw_lines}
    request.session[CART_SESSION_KEY] = {}
    request.session.pop('checkout_key', None)
    return redirect('order_track', token=order.tracking_token)


def track_landing(request):
    last = request.session.get('last_checkout')
    session_key = request.session.session_key
    if isinstance(last, dict) and session_key:
        try:
            key = UUID(last.get('key', ''))
        except (TypeError, ValueError, AttributeError):
            key = None
        if key:
            attempt = CheckoutAttempt.objects.select_related('order').filter(
                session_key=session_key, idempotency_key=key, order__isnull=False,
            ).first()
            if attempt:
                token = tracking_token_for_attempt(session_key, key)
                if token_hash(token) == attempt.order.tracking_token_hash:
                    return redirect('order_track', token=token)
    return render(request, 'orders/track_landing.html')


def track_order(request, token):
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
        raise Http404
    order = get_object_or_404(Order.objects.prefetch_related('items'), tracking_token_hash=token_hash(token))
    response = render(request, 'orders/track.html', {'order': order})
    response['Referrer-Policy'] = 'no-referrer'
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response
