from django.urls import path
from . import views

urlpatterns = [
path('delivery_agent_register/', views.delivery_agent_register, name='delivery_agent_register'),
path('delivery_agent_home/', views.delivery_agent_dashboard, name='delivery_agent_home'),
path('delivery/requests/', views.delivery_requests, name='delivery_requests'),
path('delivery/accept/<int:order_id>/', views.accept_order, name='accept_order'),
path('delivery/reject/<int:order_id>/', views.reject_order, name='reject_order'),
path('order/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
path('order/<int:order_id>/issue/', views.report_order_issue, name='report_order_issue'),
path('agent/orders/<int:order_id>/delivered/', views.mark_delivered, name='mark_delivered'),



]
