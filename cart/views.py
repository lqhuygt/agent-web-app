from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import CartQuantityForm
from .services import CART_SESSION_KEY, get_cart_entries, set_cart_quantity


def _context(request, error=''):
    entries, total = get_cart_entries(request)
    return {'entries': entries, 'total': total, 'error': error, 'max_quantity': 10}


def cart_page(request):
    return render(request, 'cart/page.html', _context(request))


def _change(request, action):
    form = CartQuantityForm(request.POST)
    error = ''
    if not form.is_valid():
        error = 'Số lượng hoặc biến thể không hợp lệ.'
    else:
        variant_id = form.cleaned_data['variant_id']
        quantity = form.cleaned_data['quantity']
        if action == 'remove':
            quantity = 0
        elif action == 'add':
            if quantity == 0:
                error = 'Số lượng phải lớn hơn 0.'
            else:
                quantity += request.session.get(CART_SESSION_KEY, {}).get(str(variant_id), 0)
        if not error:
            try:
                set_cart_quantity(request=request, variant_id=variant_id, quantity=quantity)
            except ValidationError as exc:
                error = '; '.join(exc.messages)
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'cart/_region.html', _context(request, error))
    if error:
        return render(request, 'cart/page.html', _context(request, error), status=400)
    return redirect('cart_page')


@require_POST
def add(request):
    return _change(request, 'add')


@require_POST
def update(request):
    return _change(request, 'update')


@require_POST
def remove(request):
    return _change(request, 'remove')
