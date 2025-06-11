from django.shortcuts import render
from products.models import Product
from categories.models import Category
from recommendations.utils import get_popular_products, get_personalized_recommendations

# Create your views here.

def landing_page(request):
    popular_products = get_popular_products(limit=8)
    context = {
        'smart_phones': Product.objects.filter(category__name='Smart Phones', status='approved'),
        'smart_watches': Product.objects.filter(category__name='Smart Watches', status='approved'),
        'categories': Category.objects.all(),
        'popular_products': popular_products
    }
    

    return render(request, 'landing/landing_page.html', context)
