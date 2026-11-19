from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse

from .rate_limit import allow_attempt


class AttemptRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            if request.path == reverse('admin:login'):
                kind, limit = 'admin-login', settings.FORM_ADMIN_LOGIN_LIMIT
            elif request.path == reverse('checkout'):
                kind, limit = 'checkout', settings.FORM_CHECKOUT_LIMIT
            else:
                kind = None
            if kind and not allow_attempt(
                kind=kind, identity=request.META.get('REMOTE_ADDR', ''),
                limit=limit, window_seconds=settings.FORM_RATE_WINDOW_SECONDS,
            ):
                response = HttpResponse('Quá nhiều yêu cầu. Vui lòng thử lại sau.', status=429)
                response['Retry-After'] = str(settings.FORM_RATE_WINDOW_SECONDS)
                return response
        return self.get_response(request)
