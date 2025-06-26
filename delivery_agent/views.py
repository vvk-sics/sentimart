from django.shortcuts import render, redirect
from accounts.models import User
from .models import DeliveryAgent, OrderVisibility
from products.models import Order
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render
from .utils import calculate_streak, calculate_rating
from products.models import Order
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# Create your views here.

def delivery_agent_register(request):
    context = {}

    if request.method == "POST":
        full_name = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        location = request.POST.get('location')
        pincode = request.POST.get('pincode')
        licence_number = request.POST.get('licencenumber')
        licence_expiry_date = request.POST.get('licenceexpirydate')
        driving_licence = request.FILES.get('drivinglicence')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmpassword')
        own_vehicle = request.POST.get('own_vehicle')

        errors = {}

        if not full_name:
            errors['fullname'] = "Full name is required"
        if not email:
            errors['email'] = "Email is required"
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = "Invalid email format"
        if not phone or not phone.isdigit() or len(phone) != 10:
            errors['phone'] = "Enter a valid 10-digit phone number"
        if not city:
            errors['city'] = "City is required"
        if not location:
            errors['location'] = "Location is required"
        if not pincode or not pincode.isdigit() or len(pincode) != 6:
            errors['pincode'] = "Enter a valid 6-digit pincode"
        if not licence_number:
            errors['licencenumber'] = "License number is required"
        if not licence_expiry_date:
            errors['licenceexpirydate'] = "Expiry date is required"
        if not password or len(password) < 6 or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
            errors['password'] = "Password must be at least 6 characters, contain an uppercase letter and a number"
        if password != confirm_password:
            errors['confirmpassword'] = "Passwords do not match"
        if not driving_licence:
            errors['drivinglicence'] = "Upload your license"
        if own_vehicle not in ['True', 'False']:
            errors['own_vehicle'] = "Select an option"

        if errors:
            context['errors'] = errors
            context['form_data'] = request.POST
            return render(request, 'delivery_agent/agent_register.html', context)

        user = User.objects.create_user(username=full_name, email=email, password=password, is_active=False)
        user.user_type = 'delivery_agent'
        user.save()

        DeliveryAgent.objects.create(
            user=user,
            phone=phone,
            city=city,
            location=location,
            pincode=pincode,
            licence_number=licence_number,
            licence_expiry_date=licence_expiry_date,
            driving_licence=driving_licence,
            own_vehicle=own_vehicle
        )

        messages.success(request, "Registration successful! Please wait for admin approval.")
        return redirect('login')

    return render(request, 'delivery_agent/agent_register.html', context)

@login_required
def delivery_agent_dashboard(request):
    if not hasattr(request.user, 'delivery_agent_profile'):
        return redirect('login')
    
    agent = request.user.delivery_agent_profile
    agent.update_login_streak()
    
    # Get today's deliverable orders (using created_at instead of delivery_date)
    today = timezone.now().date()
    deliverable_today = Order.objects.filter(
        assigned_to=agent,
        status='Shipped',
        created_at__date=today
    ).count()
    
    context = {
        'login_streak': agent.login_streak,
        'deliverable_today': deliverable_today,
        'agent_rating': calculate_rating(agent),
    }
    return render(request, 'delivery_agent/agent_dashboard.html', context)

def delivery_requests(request):
    agent = DeliveryAgent.objects.get(user=request.user)
    orders = Order.objects.filter(assigned_to=agent, is_assigned=True).exclude(status='Delivered')
    return render(request, 'delivery_agent/delivery_requests.html', {'orders': orders})

@login_required
def accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.assigned_to.user == request.user:
        order.status = 'About to Deliver'
        order.save()
    return redirect('delivery_requests')

    # return redirect(f"{reverse('delivery_requests')}?status=pending")

def reject_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    issue_reason = request.POST.get('issue_reason')
    if order.assigned_to.user == request.user:
        order.status = 'Rejected'
        order.issue_reason = issue_reason
        order.save()
    return redirect('delivery_requests')

@login_required
def mark_as_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.assigned_to.user == request.user:
        order.status = 'Delivered'
        order.save()
    return redirect('delivery_requests')

@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_to__user=request.user)
    new_status = request.POST.get('new_status')

    if new_status in ['transit', 'delivered']:
        order.status = new_status
        order.save()

    return redirect(f"{reverse('delivery_requests')}")

@require_POST
def report_order_issue(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_to__user=request.user)

    issue_reason = request.POST.get('issue_reason')
    notes = request.POST.get('additional_notes')

    order.issue_reason = f"{issue_reason} - {notes}"
    order.status = 'pending'
    order.save()

    return redirect(f"{reverse('delivery_dashboard')}")

@login_required
def mark_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_to=request.user.delivery_agent_profile)
    if order.status == 'About to Deliver':
        order.status = 'Delivered'
        order.save()
        messages.success(request, "Order marked as Delivered.")
    else:
        messages.error(request, "Order is not ready to be marked as Delivered.")
    return redirect('delivery_requests')