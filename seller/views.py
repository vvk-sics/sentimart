from django.shortcuts import render, redirect
from .models import Seller
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from products.models import Product, ProductAttribute, ProductAttributeValue, ProductVariant
from categories.models import Category
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  

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

@login_required
@never_cache
def seller_dashboard(request):
    return render(request, 'seller/seller_dashboard.html')

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
            stock=stock
        )
        return redirect('add_variants', product_id=product.id)
    
    categories = Category.objects.all()
    return render(request, 'seller/add_product.html', {'categories': categories})

def add_variants(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        selected_values = request.POST.getlist('attribute_values')

        variant = ProductVariant.objects.create(product=product, price=price, stock=stock)
        variant.attributes.set(selected_values)
        variant.save()

        messages.success(request, "Variant added successfully.")
        return redirect('add_variants', product_id=product.id)

    attribute_values = ProductAttributeValue.objects.all()
    return render(request, 'seller/add_variants.html', {
        'product': product,
        'attribute_values': attribute_values
    })

def add_product_attribute(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            ProductAttribute.objects.create(name=name)
            messages.success(request, 'Attribute created successfully!')
            return redirect('add_product_attribute')
    return render(request, 'seller/add_attribute.html')


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
