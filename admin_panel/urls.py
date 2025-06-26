from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='admin_dashboard'),
    path('seller-requests/', views.seller_requests, name='seller_requests'),
    path('seller-request/<int:seller_id>/', views.seller_request_detail, name='seller_request_detail'),
    path('sellers/', views.sellers_list, name='sellers-list'),
    path('seller/<int:seller_id>/', views.seller_view, name='seller_view'),
    path('buyers/', views.buyers_list, name='buyers-list'),
    path('sellers/toggle/<int:seller_id>/', views.toggle_seller_status, name='toggle-seller'),
    path('seller/reject/<int:seller_id>/', views.seller_reject_reason, name='seller_reject_reason'),
    path('add_category/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/,', views.delete_category, name='delete_category'),

    path('manage_products/', views.manage_products, name='manage_products'),
    path('admin/approve-product/<int:product_id>/', views.approve_product, name='approve_product'),
    path('admin/reject-product/<int:product_id>/', views.reject_product, name='reject_product'),
    path('low_stock_products/', views.low_stock_products, name='low_stock_products'),

    path('order_management', views.order_management, name='order_management'),
    path('admin/ship/<int:order_id>/', views.ship_order, name='ship_order'),

    path('delivery-agents/', views.delivery_agents_list, name='delivery-agents-list'),
    path('delivery-agent/<int:agent_id>/', views.delivery_agent_view, name='delivery-agent-view'),
    path('toggle-agent/<int:agent_id>/', views.toggle_agent_status, name='toggle-agent'),
    path('agent-requests/', views.agent_requests, name='agent-requests'),
    path('agent-request/<int:agent_id>/', views.agent_request_detail, name='agent-request-detail'),
    path('agent-reject/<int:agent_id>/', views.agent_reject_reason, name='agent-reject-reason'),

    


]
