from django.utils import timezone
from datetime import timedelta
from .models import DeliveryAgent

def calculate_streak(user):
    """
    Calculate consecutive login days streak for delivery agent
    """
    try:
        agent = DeliveryAgent.objects.get(user=user)
        last_login = user.last_login.date() if user.last_login else None
        today = timezone.now().date()
        
        if not last_login:
            return 0
            
        # Check if logged in today or yesterday to maintain streak
        if last_login == today:
            return agent.login_streak or 1
        elif last_login == today - timedelta(days=1):
            return (agent.login_streak or 0) + 1
        else:
            return 0
    except DeliveryAgent.DoesNotExist:
        return 0

def calculate_rating(agent):
    """
    Calculate average rating for delivery agent based on delivered orders
    """
    from products.models import Order
    
    delivered_orders = Order.objects.filter(
        assigned_to=agent,
        status='Delivered'
    ).exclude(delivery_rating__isnull=True)
    
    if not delivered_orders.exists():
        return 4.5  # Default rating if no ratings yet
    
    total_ratings = sum(order.delivery_rating for order in delivered_orders)
    average_rating = total_ratings / delivered_orders.count()
    return round(average_rating, 1)