from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.menu_items),
    path('categories', views.categories),
    path('menu-items/<str:pk>', views.single_item),
    path('groups/manager/users', views.managers), 
    path('groups/manager/users/<str:pk>', views.manager_delete), 
    path('groups/delivery-crew/users', views.delivery), 
    path('groups/delivery-crew/users/<str:pk>', views.delivery_delete), 
    path('cart/menu-items', views.cart_menu_items),
    path('orders', views.orders),
    path('orders/<str:pk>', views.order_detail),
]
