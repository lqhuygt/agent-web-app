from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Stock, StockMovement


@transaction.atomic
def adjust_stock(*, variant_id: int, delta: int, reason: str, actor) -> StockMovement:
    if not actor or not actor.is_authenticated or not actor.has_perm('inventory.adjust_stock'):
        raise PermissionDenied('Stock adjustment permission required.')
    if not isinstance(delta, int) or isinstance(delta, bool) or delta == 0:
        raise ValidationError('Adjustment must be a nonzero integer.')
    reason = reason.strip()
    if not reason or len(reason) > 255:
        raise ValidationError('A reason of at most 255 characters is required.')
    Stock.objects.get_or_create(variant_id=variant_id)
    stock = Stock.objects.select_for_update().get(variant_id=variant_id)
    before = stock.quantity
    after = before + delta
    if after < 0:
        raise ValidationError('Insufficient stock.')
    stock.quantity = after
    stock.save(update_fields=['quantity'])
    return StockMovement.objects.create(
        variant_id=variant_id, delta=delta, before=before, after=after, reason=reason, actor=actor
    )
