from django.contrib import admin

from .forms import ProductImageForm
from .models import Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('color', 'size', 'sku', 'active')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageForm
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'active')
    list_filter = ('active', 'category')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (ProductVariantInline, ProductImageInline)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'color', 'size', 'active')
    list_filter = ('active', 'product')
    search_fields = ('sku', 'product__name')
