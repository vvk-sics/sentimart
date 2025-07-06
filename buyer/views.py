from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from .models import Buyer, Address
from django.contrib import messages
from categories.models import Category  
from products.models import Product, CartItem, Order, OrderItem, ProductVariant, ProductAttribute, ProductAttributeValue, Invoice
from categories.models import Category
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
from django.db.models import Q
from django.http import HttpResponseForbidden
from .forms import ReviewForm
from django.urls import reverse
from django.template.loader import get_template
import uuid
from recommendations.models import UserProductInteraction
from recommendations.utils import get_popular_products, get_personalized_recommendations
from django.db.models import Avg
# Create your views here.

def buyer_register(request):
    context = {}
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        errors = {}

        if not username:
            errors['username'] = "Username is required."
        if not email:
            errors['email'] = "Email is required."
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            errors['phone_number'] = "Enter a valid 10-digit phone number."
        if not password or len(password) < 6:
            errors['password'] = "Password must be at least 6 characters."
        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."

        if User.objects.filter(username=username).exists():
            errors['username'] = "Username already taken."
        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already registered."

        if errors:
            context['errors'] = errors
            context['form_data'] = request.POST
            return render(request, 'buyer/buyer_register.html', context)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.user_type = 'buyer'
        user.save()
        buyer = Buyer.objects.create(user=user, phone_number=phone_number)
        buyer.save()
        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')  
    
    return render(request, 'buyer/buyer_register.html')

@login_required
@never_cache
def buyer_profile(request):
    buyer = request.user.buyer_profile
    return render(request, 'buyer/buyer_profile.html', {'buyer': buyer})

def edit_buyer_profile(request):
    buyer = request.user.buyer_profile
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')

        if not username:
            messages.error(request, 'Username is required.')
            return redirect('edit-buyer-profile')
        if not email:
            messages.error(request, 'Email is required.')
            return redirect('edit-buyer-profile')
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            messages.error(request, 'Enter a valid 10-digit phone number.')
            return redirect('edit-buyer-profile')

        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            messages.error(request, 'Username already taken.')
            return redirect('edit-buyer-profile')
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, 'Email already registered.')
            return redirect('edit-buyer-profile')

        user = User.objects.get(id=request.user.id)
        user.username = username
        user.email = email
        buyer.phone_number = phone_number
        user.save()
        buyer.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('buyer-profile')
    return render(request, 'buyer/edit_buyer_profile.html', {'buyer': buyer})

# def get_user_recommendations(user):
#     cart_cats = CartItem.objects.filter(user=user).values_list('product__category', flat=True)
#     order_cats = OrderItem.objects.filter(order__user=user).values_list('product__category', flat=True)
#     categories = list(set(cart_cats) | set(order_cats))

#     interacted_product_ids = set(
#         CartItem.objects.filter(user=user).values_list('product__id', flat=True)
#     ) | set(
#         OrderItem.objects.filter(order__user=user).values_list('product__id', flat=True)
#     )

#     if categories:
#         recommendations = Product.objects.filter(
#             category__in=categories
#         ).exclude(id__in=interacted_product_ids).distinct()[:5]
#     else:
#         # fallback to latest products
#         recommendations = Product.objects.exclude(id__in=interacted_product_ids).order_by('-id')[:5]

#     return recommendations

from django.db.models import Count
from django.db.models import Subquery, OuterRef
@login_required
@never_cache
def buyer_home(request):
    
    categories = Category.objects.all()
    popular_products = get_popular_products(limit=8)
    popular_product_ids = OrderItem.objects.values('product') \
        .annotate(order_count=Count('id')) \
        .order_by('-order_count') \
        .values_list('product', flat=True)[:1]

    best_seller = Product.objects.filter(
        id__in=Subquery(popular_product_ids),
        status='approved'
    ).first()
    

    if not best_seller and popular_products:
        best_seller = popular_products[0]
    
    query = request.GET.get('q', '').strip()
    if query:
       
        search_results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(model_number__icontains=query) |
            Q(category__name__icontains=query),
            status='approved'
        ).distinct().order_by('-created_at')
        
       
        if not search_results.exists():
            words = query.split()
            if len(words) > 1:
                q_objects = Q()
                for word in words:
                    q_objects |= (
                        Q(name__icontains=word) |
                        Q(description__icontains=word) |
                        Q(brand_name__icontains=word) |
                        Q(model_number__icontains=word) |
                        Q(category__name__icontains=word)
                    )
                search_results = Product.objects.filter(
                    q_objects,
                    status='approved'
                ).distinct().order_by('-created_at')
        
        context = {
            'is_search_page': True,
            'query': query,
            'search_results': search_results,
            'categories': categories,
            'popular_products': popular_products,
            'best_seller': best_seller,
        }
        return render(request, 'buyer/buyer_home.html', context)
  
    smart_phones = Product.objects.filter(category__name='Smart Phones', status='approved')
    smart_watches = Product.objects.filter(category__name='Smart Watches', status='approved')
    
    personalized_products = []
    if request.user.is_authenticated:
        personalized_products = get_personalized_recommendations(request.user.id, limit=8)
    
    context = {
        'is_search_page': False,
        'smart_phones': smart_phones,
        'smart_watches': smart_watches,
        'categories': categories,
        'popular_products': popular_products,
        'personalized_products': personalized_products,
        'best_seller': best_seller,
    }
    return render(request, 'buyer/buyer_home.html', context)

@csrf_exempt
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query and len(query) >= 2:
        # Product suggestions
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(brand_name__icontains=query),
            status='approved'
        )[:3]
        
        # Category suggestions
        categories = Category.objects.filter(
            name__icontains=query
        )[:2]
        
        suggestions = [
            {
                'type': 'product',
                'id': p.id,
                'name': p.name,
                'brand_name': p.brand_name,
                'url': reverse('product-detail', kwargs={'pk': p.id})
            } for p in products
        ] + [
            {
                'type': 'category',
                'id': c.id,
                'name': c.name,
                'url': reverse('category_products', kwargs={'slug': c.slug})
            } for c in categories
        ]
    
    return JsonResponse({'suggestions': suggestions})
        
from collections import defaultdict
from datetime import datetime, timedelta
@login_required
@never_cache
def product_detail(request, pk):
    product = Product.objects.get(pk=pk)
    # Track view if user is authenticated
    if request.user.is_authenticated:
        interaction, created = UserProductInteraction.objects.get_or_create(
            user=request.user,
            product=product
        )
        interaction.view_count += 1
        interaction.save()
    variants = product.variants.prefetch_related('attributes__attribute').all()
    attributes_dict = defaultdict(set)
    for variant in variants:
        for attr_value in variant.attributes.all():
            attributes_dict[attr_value.attribute.name].add(attr_value.value)

   
    attributes_data = [
        {"name": name, "values": sorted(list(values))}
        for name, values in attributes_dict.items()
    ]

    avg_rating = product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    rating_count = product.reviews.count()

    today = datetime.today()
    delivery_date = today + timedelta(days=7)


    return render(request, "buyer/product_detail.html", {
        "product": product,
        "attributes": attributes_data,
        'avg_rating': round(avg_rating, 1),
        'rating_count': rating_count,
        'delivery_date': delivery_date,
    })
    

@login_required
@never_cache
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))

    selected_attrs = []
    for key, value in request.POST.items():
        if key not in ['csrfmiddlewaretoken', 'quantity']:
            try:
                attr = ProductAttribute.objects.get(name=key)
                attr_val = ProductAttributeValue.objects.get(attribute=attr, value=value)
                selected_attrs.append(attr_val.id)
            except ProductAttributeValue.DoesNotExist:
                messages.error(request, "Invalid product attribute selected.")
                return redirect('product-detail', pk=product_id)

    variants = ProductVariant.objects.filter(product=product)
    matched_variant = None

    for variant in variants:
        variant_attr_ids = set(variant.attributes.values_list('id', flat=True))
        if set(selected_attrs) == variant_attr_ids:
            matched_variant = variant
            break

    if not matched_variant:
        messages.error(request, "Selected variant does not exist.")
        return redirect('product-detail', pk=product_id)

    if quantity > matched_variant.stock:
        messages.error(request, "Not enough stock for the selected variant.")
        return redirect('product-detail', pk=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        variant=matched_variant,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    matched_variant.stock -= quantity
    matched_variant.save()
    print("Selected attribute IDs:", selected_attrs)
    print("Variant attributes:", list(variant.attributes.values_list('id', flat=True)))
    messages.success(request, "Product added to cart.")
    return redirect('product-detail', pk=product_id)

@login_required
@never_cache
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'buyer/cart.html', {'cart_items': cart_items, 'total': total})



@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('cart')

    buyer = request.user.buyer_profile
    default_address = buyer.addresses.filter(is_default=True).first()

    if request.method == 'POST':
        if not default_address:
            messages.error(request, "No default address set.")
            return redirect('address_list')

        total = sum(item.product.base_price * item.quantity for item in cart_items)

        for item in cart_items:
            if item.quantity > item.product.stock:
                messages.error(request, f"Not enough stock for {item.product.name}.")
                return redirect('cart')

        # Create order but don't process it yet
        order = Order.objects.create(
            user=request.user,
            delivery_address=default_address,
            total_price=total,
            status='pending_payment'  # Add this status to your Order model
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.base_price
            )

        # Store order ID in session for payment processing
        request.session['current_order_id'] = order.id
        
        return redirect('payment')

    total_price = sum(item.product.base_price * item.quantity for item in cart_items)
    return render(request, 'buyer/place_order.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'default_address': default_address
    })

# Add these new views for payment handling
@login_required
def payment(request):
    order_id = request.session.get('current_order_id')
    if not order_id:
        return redirect('cart')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        # Get payment method
        payment_method = request.POST.get('payment_method')
        # Update order with payment method
        order.payment_method = payment_method
        order.status = 'processing'
        order.save()
        
        # Clear cart
        CartItem.objects.filter(user=request.user).delete()
        
        # Clear session
        if 'current_order_id' in request.session:
            del request.session['current_order_id']
        
        # Create invoice
        Invoice.objects.create(order=order, invoice_id=str(uuid.uuid4())[:8].upper())
        
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'buyer/payment.html', {
        'order': order,
    })

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    invoice = get_object_or_404(Invoice, order=order)
    return render(request, 'buyer/order_success.html', {
        'order': order,
        'invoice': invoice,
    })

# Dummy payment webhook (for simulation)
@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        # In a real app, you'd verify the payment here
        # For demo, we'll just return success
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def view_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    invoice = get_object_or_404(Invoice, order=order)
    
    return render(request, 'buyer/invoice_template.html', {
        'order': order,
        'invoice': invoice,
    })


def update_cart_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            new_quantity = data.get('quantity')

            if not item_id or not new_quantity:
                return JsonResponse({'error': 'Missing item ID or quantity'}, status=400)

            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            product = cart_item.product

            if new_quantity > 0 and new_quantity <= product.stock:
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                return JsonResponse({'error': 'Invalid quantity'}, status=400)

    
            cart_items = CartItem.objects.filter(user=request.user)
            total = sum(item.product.price * item.quantity for item in cart_items)

            return JsonResponse({'message': 'Quantity updated', 'total': total})
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')


# def search_products(request):
#     query = request.GET.get('q', '')
#     search_results = Product.objects.filter(
#         Q(name__icontains=query) |
#         Q(description__icontains=query) |
#         Q(brand_name__icontains=query) |
#         Q(model_number__icontains=query)
#     )

#     recommendations = []
#     if request.user.is_authenticated:
#         recommendations = get_user_recommendations(request.user)

#     return render(request, 'buyer/buyer_home.html', {
#         'query': query,
#         'search_results': search_results,
#         'recommendations': recommendations,
#     })


def smart_phones(request):
    return render(request, 'buyer/smartphones.html')

@login_required
def category_products(request, slug):
    category = Category.objects.get(slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'buyer/Category_products.html', {
        'category': category,
        'products': products
    })

@login_required
def orders(request):
    status = request.GET.get('status')
    if status:
        orders = Order.objects.filter(user=request.user, status=status)
    else:
        orders = Order.objects.filter(user=request.user)

    return render(request, 'buyer/orders.html', {
        'orders': orders,
        'current_status': status or 'all'
    })

@login_required
def track_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Ensure only the owner can track
    if order.user != request.user:
        return HttpResponseForbidden("You are not allowed to view this order.")

    # Handle cancellation
    if request.method == 'POST' and 'cancel' in request.POST:
        if order.status not in ['delivered', 'cancelled']:
            order.status = 'cancelled'
            order.save()
        return redirect('track_order', order_id=order.id)

    return render(request, 'buyer/track_order.html', {'order': order})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return redirect(reverse('product-detail', kwargs={'pk': product.id}))
    else:
        form = ReviewForm()

    return render(request, 'buyer/add_review.html', {'product': product, 'form': form})

@login_required
def add_address(request):
    if request.method == "POST":
        buyer = request.user.buyer_profile
        name = request.POST.get('name')
        phone = request.POST.get('phone_number')
        street = request.POST.get('street_address')
        apartment = request.POST.get('apartment')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        is_default = bool(request.POST.get('is_default'))

        if is_default:
            buyer.addresses.update(is_default=False)

        Address.objects.create(
            buyer=buyer,
            name=name,
            phone_number=phone,
            street_address=street,
            apartment=apartment,
            city=city,
            state=state,
            zip_code=zip_code,
            is_default=is_default
        )

        return redirect('address_list')

    return render(request, 'buyer/add_address.html')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, buyer=request.user.buyer_profile)

    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        street_address = request.POST.get('street_address')
        apartment = request.POST.get('apartment')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')

        if not all([name, phone_number, street_address, city, state, zip_code]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('edit_address', address_id=address.id)

        address.name = name
        address.phone_number = phone_number
        address.street_address = street_address
        address.apartment = apartment
        address.city = city
        address.state = state
        address.zip_code = zip_code
        address.save()

        messages.success(request, "Address updated successfully.")
        return redirect('address_list')

    return render(request, 'buyer/edit_address.html', {'address': address})

@login_required
def address_list(request):
    buyer = request.user.buyer_profile
    addresses = buyer.addresses.all()
    return render(request, 'buyer/address_list.html', {'addresses': addresses})

@login_required
def set_default_address(request, address_id):
    buyer = request.user.buyer_profile
    buyer.addresses.update(is_default=False)
    Address.objects.filter(id=address_id, buyer=buyer).update(is_default=True)
    return redirect('address_list')

@login_required
def delete_address(request, address_id):
    Address.objects.filter(id=address_id, buyer=request.user.buyer_profile).delete()
    return redirect('address_list')
