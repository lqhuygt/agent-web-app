from django.urls import path

from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('orders/track/', views.track_landing, name='order_track_landing'),
    path('orders/track/<str:token>/', views.track_order, name='order_track'),
]
