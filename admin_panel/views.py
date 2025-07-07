from django.shortcuts import render, redirect, get_object_or_404
from seller.models import Seller
from buyer.models import Buyer
from delivery_agent.models import DeliveryAgent
from categories.models import Category
from products.models import Product, Order
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
# Create your views here.

@login_required
@never_cache
def dashboard(request):
    sellers_count = Seller.objects.filter(is_approved=True).count()
    buyer_count = Buyer.objects.count()
    delivery_agent_count = DeliveryAgent.objects.count()
    sellers_request_count = Seller.objects.filter(is_approved=False, is_rejected=False).count()
    
    # Sales data
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)
    
    # Revenue calculations
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    weekly_revenue = Order.objects.filter(
        created_at__date__gte=start_week
    ).aggregate(total=Sum('total_price'))['total'] or 0
    monthly_revenue = Order.objects.filter(
        created_at__date__gte=start_month
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Order counts
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Best selling products (last 30 days)
    best_sellers = Product.objects.annotate(
    total_sold=Sum('orderitems__quantity')
    ).filter(
        orderitems__order__created_at__gte=timezone.now()-timedelta(days=30)
    ).order_by('-total_sold')[:5]
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(stock__lt=10)[:5]
    
    context = {
        'sellers_count': sellers_count,
        'sellers_request_count': sellers_request_count,
        'buyer_count': buyer_count,
        'delivery_agent_count': delivery_agent_count,
        'total_revenue': total_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'best_sellers': best_sellers,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'today': today,
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)

@login_required
@never_cache
def seller_requests(request):
    sellers = Seller.objects.filter(is_approved=False, is_rejected=False)
    return render(request, 'admin_panel/sellers_requests.html', {'sellers': sellers})

@login_required
@never_cache
def seller_request_detail(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            seller.is_approved = True
            seller.save()
        elif action == 'reject':
            reason = request.POST.get('reason', '')
            seller.is_rejected = True
            seller.rejection_reason = reason
            seller.save()
        return redirect('seller_requests')

    return render(request, 'admin_panel/seller_request_viewmore.html', {'seller': seller})

@login_required
@never_cache
def seller_reject_reason(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        seller.is_rejected = True
        seller.rejection_reason = reason
        seller.save()
        return redirect('seller_requests') 
    return render(request, 'admin_panel/seller_reject_reason.html', {'seller': seller})

@login_required
@never_cache
def seller_view(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    return render(request, 'admin_panel/seller_view.html', {'seller': seller})

@login_required
@never_cache
def sellers_list(request):
    sellers = Seller.objects.filter(is_approved=True)
    return render(request, 'admin_panel/sellers.html', {'sellers': sellers})

@login_required
@never_cache
def toggle_seller_status(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    user = seller.user
    user.is_active = not user.is_active
    user.save()
    return redirect('sellers-list')

@login_required
@never_cache
def buyers_list(request):
    buyers = Buyer.objects.all()
    return render(request, 'admin_panel/buyers.html', {'buyers': buyers})

@login_required
@never_cache
def delivery_agents_list(request):
    agents = DeliveryAgent.objects.all()
    return render(request, 'admin_panel/delivery_agents.html', {'agents': agents})

@login_required
@never_cache
def delivery_agent_view(request, agent_id):
    agent = get_object_or_404(DeliveryAgent, id=agent_id)
    return render(request, 'admin_panel/delivery_agent_view.html', {'agent': agent})

@login_required
@never_cache
def toggle_agent_status(request, agent_id):
    agent = get_object_or_404(DeliveryAgent, id=agent_id)
    user = agent.user
    user.is_active = not user.is_active
    user.save()
    return redirect('delivery-agents-list')

@login_required
@never_cache
def agent_requests(request):
    agents = DeliveryAgent.objects.filter(is_approved=False, is_rejected=False)
    return render(request, 'admin_panel/agent_requests.html', {'agents': agents})

@login_required
@never_cache
def agent_request_detail(request, agent_id):
    agent = get_object_or_404(DeliveryAgent, id=agent_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            agent.is_approved = True
            agent.save()
        elif action == 'reject':
            reason = request.POST.get('reason', '')
            agent.is_rejected = True
            agent.rejection_reason = reason
            agent.save()
        return redirect('agent_requests')

    return render(request, 'admin_panel/agent_request_viewmore.html', {'agent': agent})

@login_required
@never_cache
def agent_reject_reason(request, agent_id):
    agent = get_object_or_404(DeliveryAgent, id=agent_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        agent.is_rejected = True
        agent.rejection_reason = reason
        agent.save()
        return redirect('agent_requests') 
    return render(request, 'admin_panel/agent_reject_reason.html', {'agent': agent})

@login_required
@never_cache
def add_category(request):
    categories = Category.objects.all()
    errors = {}
    
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
      
        if not name:
            errors['name'] = 'Category name is required'
        if not image:
            errors['image'] = 'Category image is required'
        
        if not errors:
            try:
                Category.objects.create(name=name, image=image)
                messages.success(request, 'Category added successfully!')
                return redirect('add_category')
            except Exception as e:
                messages.error(request, f'Error adding category: {str(e)}')
        else:
            request.session['submitted_name'] = name
    
    submitted_name = request.session.pop('submitted_name', '')
    
    return render(request, 'admin_panel/add_category.html', {
        'categories': categories,
        'errors': errors,
        'submitted_name': submitted_name
    })

def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    errors = {}
    
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        # Validate inputs
        if not name:
            errors['name'] = 'Category name is required'
        
        if not errors:
            try:
                category.name = name
                if image:  # Only update image if new one was provided
                    category.image = image
                category.save()
                messages.success(request, 'Category updated successfully!')
                return redirect('add_category')  # Redirect back to category management
            except Exception as e:
                messages.error(request, f'Error updating category: {str(e)}')
    
    return render(request, 'admin_panel/edit_category.html', {
        'category': category,
        'errors': errors
    })

def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('add_category')

@login_required
@never_cache
def approve_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.status = 'approved'
    product.rejection_reason = None
    product.save()
    messages.success(request, 'Product approved successfully.')
    return redirect(f"{reverse('manage_products')}?status=pending")


@login_required
@never_cache
def reject_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        product.status = 'rejected'
        product.rejection_reason = reason
        product.save()
        messages.success(request, 'Product rejected with reason.')
        return redirect('manage_products')
    return render(request, 'admin_panel/reject_reason.html', {'product': product})

@login_required
@never_cache
def manage_products(request):
    status = request.GET.get('status')
    if status:
        products = Product.objects.filter(status=status)
    else:
        products = Product.objects.filter(seller=request.user)
    return render(request, 'admin_panel/manage_products.html', {'products': products})

@login_required
@never_cache
def low_stock_products(request):
    status=request.GET.get('status')
    if status=='low_stock':
        low_stock_products = Product.objects.filter(stock__lt=10, stock__gt=0)
    elif status=='out_of_stock':
        low_stock_products = Product.objects.filter(stock=0)
    else:
        low_stock_products = Product.objects.filter(stock__lt=10)
    return render(request, 'admin_panel/low_stock_products.html', {'low_stock_products': low_stock_products})

def order_management(request):
    status = request.GET.get('status')
    if status:
        orders = Order.objects.filter(status=status).prefetch_related('items__product')
    else:
        orders = Order.objects.filter(status='Pending').prefetch_related('items__product')
    agents = DeliveryAgent.objects.all()
    return render(request, 'admin_panel/order_management.html',  {'orders': orders, 'agents': agents})

def ship_order(request, order_id):
    if request.method == 'POST':
        
        agent_id = request.POST.get('agent')

        if not agent_id:
            messages.error(request, "Please select a delivery agent.")
            return redirect('order_management')
        try:
            agent = DeliveryAgent.objects.get(id=agent_id)
        except DeliveryAgent.DoesNotExist:
            messages.error(request, "Selected delivery agent does not exist.")
            return redirect('order_management')
        
        order = get_object_or_404(Order, id=order_id)

        order.status = 'Shipped'
        order.assigned_to = agent
        order.is_assigned = True
        order.save()
        messages.success(request, "Order shipped and agent assigned.")
    return redirect('order_management')