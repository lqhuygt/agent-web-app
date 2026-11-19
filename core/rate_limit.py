import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import RateLimitBucket


@transaction.atomic
def allow_attempt(*, kind: str, identity: str, limit: int, window_seconds: int) -> bool:
    if limit <= 0:
        return True
    key = hmac.new(settings.SECRET_KEY.encode(), f'{kind}:{identity}'.encode(), hashlib.sha256).hexdigest()
    now = timezone.now()
    bucket, _ = RateLimitBucket.objects.get_or_create(
        key=key, defaults={'count': 0, 'window_started_at': now},
    )
    bucket = RateLimitBucket.objects.select_for_update().get(pk=bucket.pk)
    if now >= bucket.window_started_at + timedelta(seconds=window_seconds):
        bucket.count = 0
        bucket.window_started_at = now
    if bucket.count >= limit:
        return False
    bucket.count += 1
    bucket.save(update_fields=['count', 'window_started_at'])
    return True
