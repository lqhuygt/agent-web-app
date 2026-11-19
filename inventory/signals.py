from django.db.models.signals import post_save
from django.dispatch import receiver

from catalog.models import ProductVariant

from .models import Stock


@receiver(post_save, sender=ProductVariant)
def create_zero_stock_for_variant(sender, instance, created, **kwargs):
    if created:
        Stock.objects.get_or_create(variant=instance)
