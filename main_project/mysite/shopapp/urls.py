from django.contrib.auth.decorators import login_required
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShopIndexView,
    GroupsListView,
    ProductDetailsView,
    ProductsListView,
    OrdersListView,
    OrderDetailView,
    OrderCreateView,
    OrderUpdateView,
    OrderDeleteView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    create_order,
    ProductsDataExportView,
    OrdersDataExportView,
    ProductsApi,
    OrdersApi,
    ProductViewSet,
    OrdersViewSet, LatestProductsFeed, UserOrdersListView, UserOrdersExportView,
)

app_name = 'shopapp'

routers = DefaultRouter()
routers.register('products', ProductViewSet)
routers.register('orders', OrdersViewSet)


urlpatterns = [
    path('', ShopIndexView.as_view(), name='index'),
    path('groups/', GroupsListView.as_view(), name='groups_list'),
    path('products/', ProductsListView.as_view(), name='products_list'),
    path('products/export/', ProductsDataExportView.as_view(), name='products-export'),
    path('products/create', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', ProductDetailsView.as_view(), name='product_details'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/confirm-archive/', ProductDeleteView.as_view(), name='product_delete'),
    path('orders/create', OrderCreateView.as_view(), name='order_create'),
    path('orders/', OrdersListView.as_view(), name='orders_list'),
    path('orders/export/', OrdersDataExportView.as_view(), name='orders-export'),
    path('orders/<int:pk>', OrderDetailView.as_view(), name='order_details'),
    path('orders/<int:pk>/update', OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/archive', OrderDeleteView.as_view(), name='order_delete'),
    path('orders/create', create_order, name='orders_create'),

    path('products/api', ProductsApi.as_view(), name='products_api'),
    path('orders/api', OrdersApi.as_view(), name='orders_api'),
    path('api/', include(routers.urls)),

    path('latest/feed/', LatestProductsFeed(), name='products_feed'),

    path('users/<int:user_id>/orders/', login_required(UserOrdersListView.as_view()), name='users_orders'),
    path('users/<int:user_id>/orders/export/', UserOrdersExportView.as_view(), name='user_orders_export')

]