from django.shortcuts import render, redirect
from accounts.models import User
from .models import DeliveryAgent, OrderVisibility
from products.models import Order
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages

# Create your views here.

def delivery_agent_register(request):
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
        own_vehicle = request.POST.get('own_vehicle')

        user = User.objects.create_user(username=full_name, email=email, password=password)
        user.user_type = 'delivery_agent'
        user.save()

        agent = DeliveryAgent.objects.create(
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

        return redirect('login')

    return render(request, 'delivery_agent/agent_register.html')

def delivery_agent_dashboard(request):
    return render(request, 'delivery_agent/agent_dashboard.html')

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