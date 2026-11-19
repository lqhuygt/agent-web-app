from django.urls import path

from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('orders/track/<str:token>/', views.track_order, name='order_track'),
]
