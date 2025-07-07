from django.shortcuts import render, redirect
from .models import Seller
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from products.models import Product, ProductAttribute, ProductAttributeValue, ProductVariant, OrderItem, Order
from categories.models import Category
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt 
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum 
from django.db.models.functions import Coalesce

@never_cache
def seller_registration(request):
    context = {}
    if request.method == "POST":
        full_name = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        business_name = request.POST.get('displayname')
        business_address = request.POST.get('businessaddress')
        business_type = request.POST.get('businesstype')
        registration_number = request.POST.get('registernumber')
        validation_doc = request.FILES.get('validationdoc')

        errors = {}

        if not full_name:
            errors['fullname'] = "Full name is required."
        if not email:
            errors['email'] = "Email is required."
        elif User.objects.filter(email=email).exists():
            errors['email'] = "Email already registered."
        if not password or len(password) < 6:
            errors['password'] = "Password must be at least 6 characters."
        if not phone or not phone.isdigit() or len(phone) != 10:
            errors['phone'] = "Enter a valid 10-digit phone number."
        if not business_name:
            errors['displayname'] = "Business name is required."
        if not business_type:
            errors['businesstype'] = "Business type is required."
        if not business_address:
            errors['businessaddress'] = "Business address is required."
        if not registration_number:
            errors['registernumber'] = "Registration number is required."
        if not validation_doc:
            errors['validationdoc'] = "Please upload a validation document."

        if errors:
            context['errors'] = errors
            context['form_data'] = request.POST
            return render(request, 'seller/seller_registration.html', context)

        user = User.objects.create_user(username=full_name, email=email, password=password)
        user.user_type = 'seller'
        user.save()

        Seller.objects.create(
            user=user,
            phone_number=phone,
            business_name=business_name,
            business_type=business_type,
            business_address=business_address,
            registration_number=registration_number,
            validation_document=validation_doc
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'seller/seller_registration.html')

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            request.session['reset_email'] = email  
            return redirect('reset_password')
        except User.DoesNotExist:
            messages.error(request, "Email does not exist.")
    
    return render(request, 'seller/forgot-password.html')


def reset_password(request):
    if 'reset_email' not in request.session:
        return redirect('forgot_password')  
    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            user = User.objects.get(email=request.session['reset_email'])
            user.set_password(password)
            user.save()
            del request.session['reset_email'] 
            messages.success(request, "Password reset successfully. You can now log in.")
            return redirect('login')

    return render(request, 'seller/reset_password.html')

@login_required
@never_cache
def seller_dashboard(request):
    if request.user.user_type != 'seller':
        return redirect('dashboard')
    
    seller = request.user
    products = Product.objects.filter(seller=seller)
    
    order_items = OrderItem.objects.filter(product__seller=seller).select_related('order', 'product')
    
    total_sales = sum(item.price * item.quantity for item in order_items)
    
    new_orders = order_items.filter(
        order__created_at__gte=timezone.now()-timedelta(days=7)
    ).values('order').distinct().count()
    
    customer_ids = order_items.values_list('order__user', flat=True).distinct()
    customers = len(customer_ids)
    
 
    best_sellers = products.annotate(
        total_sold=Coalesce(Sum('orderitems__quantity'), 0)
    ).order_by('-total_sold')[:6]
    
    
    low_stock = products.filter(stock__lt=10)
    
  
    recent_orders = Order.objects.filter(
        id__in=order_items.values_list('order', flat=True).distinct()
    ).order_by('-created_at')[:6]
    
    context = {
        'total_sales': total_sales,
        'new_orders': new_orders,
        'customers': customers,
        'best_sellers': best_sellers,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
    }
    return render(request, 'seller/seller_dashboard.html', context)

@login_required
@never_cache
def seller_profile(request):
    seller = request.user.seller_profile
    return render(request, 'seller/seller_profile.html', {'seller': seller})



@login_required
@never_cache
def edit_seller_profile(request):
    seller = request.user.seller_profile

    if request.method == 'POST':
        seller.user.username = request.POST.get('username')
        seller.user.email = request.POST.get('email')
        seller.user.save()
        seller.phone_number = request.POST.get('phone_number')
        seller.business_name = request.POST.get('business_name')
        seller.business_type = request.POST.get('business_type')
        seller.business_address = request.POST.get('business_address')
        seller.registration_number = request.POST.get('registration_number')

        if request.FILES.get('validation_document'):
            seller.validation_document = request.FILES.get('validation_document')

        seller.save()
        return redirect('seller_profile')

    return render(request, 'seller/edit_seller_pro.html', {'seller': seller})

def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        brand_name = request.POST.get('brand_name')
        model_number = request.POST.get('model_number')
        category_id = request.POST.get('category')
        sub_category = request.POST.get('sub_category')
        base_price = request.POST.get('base_price')
        discount = request.POST.get('discount')
        image = request.FILES.get('image')
        stock = request.POST.get('stock')
        sku = request.POST.get('sku')

        category = get_object_or_404(Category, id=category_id)

        product = Product.objects.create(
            seller=request.user,
            name=name,
            description=description,
            brand_name=brand_name,
            model_number=model_number,
            category=category,
            sub_category=sub_category,
            base_price=base_price,
            discount=discount,
            image=image,
            stock=stock,
            sku=sku
        )
        return redirect('add_variants', product_id=product.id)
    
    categories = Category.objects.all()
    return render(request, 'seller/add_product.html', {'categories': categories})

def add_variants(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    allowed_attributes = product.category.attributes.prefetch_related('values').all()
    for i in allowed_attributes:
        print(i.values)

    if request.method == 'POST':
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        selected_values = request.POST.getlist('attribute_values')

        # Validate all required attributes are selected
        selected_attrs = ProductAttributeValue.objects.filter(
            id__in=selected_values
        ).values_list('attribute_id', flat=True)
        
        required_attrs = set(allowed_attributes.values_list('id', flat=True))
        selected_attrs_set = set(selected_attrs)
        
        if len(selected_values) != len(required_attrs) or selected_attrs_set != required_attrs:
            messages.error(request, "Please select exactly one value for each required attribute.")
            return redirect('add_variants', product_id=product.id)

        # Check for existing variant with exactly these attributes
        existing_variants = ProductVariant.objects.filter(product=product).prefetch_related('attributes')
        for variant in existing_variants:
            variant_attrs = {attr.id for attr in variant.attributes.all()}
            selected_attrs = {int(val) for val in selected_values}
            if variant_attrs == selected_attrs:
                messages.error(request, "A variant with these exact attributes already exists.")
                return redirect('add_variants', product_id=product.id)

        # Create new variant
        variant = ProductVariant.objects.create(
            product=product, 
            price=price, 
            stock=stock
        )
        variant.attributes.set(selected_values)
        messages.success(request, "Variant added successfully!")
        return redirect('add_variants', product_id=product.id)

    # Prepare data for template
    attribute_groups = []
    for attr in allowed_attributes:
        attribute_groups.append({
            'id': attr.id,
            'name': attr.name,
            'values': attr.values.all()
        })

    variants = []
    for variant in product.variants.all().prefetch_related('attributes__attribute'):
        variant_data = {
            'id': variant.id,
            'price': variant.price,
            'stock': variant.stock,
            'attributes': {attr_val.attribute_id: attr_val.value for attr_val in variant.attributes.all()}
        }
        variants.append(variant_data)
    
    return render(request, 'seller/add_variants.html', {
        'product': product,
        'attribute_groups': attribute_groups,
        'variants': variants,
        'attributes': allowed_attributes
    })

def add_product_attribute(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_ids = request.POST.getlist('categories')

        if name:
            attribute = ProductAttribute.objects.create(name=name)
            attribute.categories.set(category_ids)
            attribute.save()

            messages.success(request, 'Attribute created and assigned to categories successfully!')
            return redirect('add_product_attribute')

    categories = Category.objects.all()
    return render(request, 'seller/add_attribute.html', {
        'categories': categories
    })


def add_product_attribute_value(request):
    attributes = ProductAttribute.objects.all()
    if request.method == 'POST':
        attribute_id = request.POST.get('attribute')
        value = request.POST.get('value')
        attribute = ProductAttribute.objects.get(id=attribute_id)
        ProductAttributeValue.objects.create(attribute=attribute, value=value)
        messages.success(request, 'Attribute value added successfully!')
        return redirect('add_product_attribute_value')
    return render(request, 'seller/add_attribute_value.html', {'attributes': attributes})

def view_products(request):
    status=request.GET.get('status')
    if status:
        products = Product.objects.filter(seller=request.user, status=status)
    else:
        products = Product.objects.filter(seller=request.user)
    return render(request, 'seller/view_products.html', {'products': products, 'current_status': status or 'all'})

@require_POST
@csrf_exempt
def update_stock(request):
    sku = request.POST.get('sku')
    new_stock = request.POST.get('new_stock')

    if not sku or new_stock is None:
        return JsonResponse({'success': False, 'message': 'Missing data'})

    try:
        new_stock = int(new_stock)
        product = Product.objects.get(sku=sku)
        product.stock = new_stock
        product.save()
        return JsonResponse({'success': True, 'message': 'Stock updated successfully'})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid stock value'})

@login_required
def seller_orders(request):
    if request.user.user_type != 'seller':
        return redirect('dashboard')

    seller = request.user
    order_items = OrderItem.objects.filter(product__seller=seller).select_related('order', 'product')

    context = {
        'order_items': order_items
    }
    return render(request, 'seller/seller_orders.html', context)