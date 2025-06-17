from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from products.models import Product
from recommendations.utils import get_popular_products, get_personalized_recommendations

def product_recommendations(request):
    # Get popular products
    popular_products = get_popular_products(limit=8)
    
    # Get personalized recommendations if user is authenticated
    personalized_products = []
    if request.user.is_authenticated:
        personalized_products = get_personalized_recommendations(request.user.id, limit=8)
    
    context = {
        'popular_products': popular_products,
        'personalized_products': personalized_products,
    }
    
    return render(request, 'recommendations/recommendations.html', context)