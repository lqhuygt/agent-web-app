from django.db import DatabaseError, connection
from django.http import HttpResponse


def live(request):
    return HttpResponse('ok', content_type='text/plain')


def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except DatabaseError:
        return HttpResponse('unavailable', status=503, content_type='text/plain')
    return HttpResponse('ok', content_type='text/plain')
