from django.urls import path
from . import views

urlpatterns = [
    path('seller_register/', views.seller_registration, name='seller_register'),
    path('seller_dashboard/', views.seller_dashboard, name='seller_dashboard'),
   
    path('seller_profile/', views.seller_profile, name='seller_profile'),
    path('profile/edit/', views.edit_seller_profile, name='edit-seller-profile'),

    path('add_product', views.add_product, name='add_product'),
    path('view_products/', views.view_products, name='view_products'),
    path('update-stock/', views.update_stock, name='update_stock'),
    path('add-variants/<int:product_id>/', views.add_variants, name='add_variants'),
    path('add-attribute/', views.add_product_attribute, name='add_product_attribute'),
    path('add-attribute-value/', views.add_product_attribute_value, name='add_product_attribute_value'),
    path('seller_orders/', views.seller_orders, name='seller_orders'),

    path('reset-password/', views.reset_password, name='reset_password'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),


]
