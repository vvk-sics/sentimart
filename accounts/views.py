from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from accounts.models import User

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username') 
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            elif user.user_type == 'seller' and user.seller_profile.is_approved == True:
                return redirect('seller_dashboard')
            elif user.user_type == 'user':
                return redirect('user_dashboard')
            elif user.user_type == 'buyer':
                messages.success(request, "Logged in successfully.")
                return redirect('product-search')
            elif user.user_type == 'delivery_agent':
                return redirect('delivery_agent_home')
            else:
                messages.error(request, "Not approved yet")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'accounts/login.html')



def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('landing_page')