from pathlib import Path
import unicodedata

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def normalize_search_text(value):
    value = value.casefold().replace('đ', 'd')
    value = unicodedata.normalize('NFD', value)
    return ' '.join(''.join(char for char in value if not unicodedata.combining(char)).split())


def validate_product_image(upload):
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError('Image must be 5 MiB or smaller.')
    if Path(upload.name).suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
        raise ValidationError('Only JPEG, PNG and WebP images are allowed.')
    try:
        upload.seek(0)
        with Image.open(upload) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError('Only JPEG, PNG and WebP images are allowed.')
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError('Invalid image content.') from None
    finally:
        upload.seek(0)


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=200)
    search_name = models.CharField(max_length=200, blank=True, editable=False, db_index=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    active = models.BooleanField(default=True)
    size_guide = models.TextField(blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(price__gte=0), name='product_price_nonnegative')]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_name = normalize_search_text(self.name)
        if kwargs.get('update_fields') is not None and 'name' in kwargs['update_fields']:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'search_name'}
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', validators=[validate_product_image])
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='variants')
    color = models.CharField(max_length=80)
    size = models.CharField(max_length=40)
    sku = models.CharField(max_length=80, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['product', 'color', 'size'], name='unique_product_color_size')]

    def __str__(self):
        return f'{self.sku} ({self.color}, {self.size})'
