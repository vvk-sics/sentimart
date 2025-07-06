from django.urls import path
from . import views
from django.views.generic.base import RedirectView

urlpatterns = [
    path('register/', views.buyer_register, name='buyer-register'),
    path('buyer-profile/', views.buyer_profile, name='buyer-profile'),
    path('edit-buyer-profile/', views.edit_buyer_profile, name='edit-buyer-profile'),
    path('home/', views.buyer_home, name='buyer-home'),
    path('buyer/search/', RedirectView.as_view(pattern_name='product-search', query_string=True)),
    path('search/', views.buyer_home, name='product-search'),
    path('product/<int:pk>/', views.product_detail, name='product-detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.cart_view, name='cart'),
    path('place_order/' , views.place_order, name='place_order'),
    path('update-cart-item/', views.update_cart_item, name='update-cart-item'),
    path('remove_cart_item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('smart_phones/', views.smart_phones, name='smart_phones'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('orders/', views.orders, name='orders'),
    path('track-order/<int:order_id>/', views.track_order_view, name='track_order'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('buyer/invoice/<int:order_id>/', views.view_invoice, name='view_invoice'),
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
    path('api/search/suggestions/', views.search_suggestions, name='search-suggestions'),
    path('payment/', views.payment, name='payment'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('payment/webhook/', views.payment_webhook, name='payment_webhook'),

    # path('search/', views.search_products, name='search_products'),


]
