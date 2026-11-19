from django.urls import path

from . import views

urlpatterns = [
    path('cart/', views.cart_page, name='cart_page'),
    path('cart/add/', views.add, name='cart_add'),
    path('cart/update/', views.update, name='cart_update'),
    path('cart/remove/', views.remove, name='cart_remove'),
]
