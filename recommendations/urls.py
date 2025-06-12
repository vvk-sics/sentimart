from django.urls import path
from .views import product_recommendations


urlpatterns = [
     path('recommendations/', product_recommendations, name='product_recommendations'),
]