# chatbot/utils.py
from products.models import Order
from django.utils import timezone

class ChatbotEngine:
    def __init__(self, user):
        self.user = user
    
    def process_message(self, message):
        message = message.lower().strip()
        
        # Order status queries
        if any(keyword in message for keyword in ['order status', 'where is my order', 'track order', 'order tracking']):
            return self.handle_order_status()
            
        # Product information
        elif any(keyword in message for keyword in ['prime', 'sentimart prime', 'membership']):
            return self.handle_prime_question()
            
        # Payment questions
        elif any(keyword in message for keyword in ['payment', 'refund', 'money back']):
            return self.handle_payment_questions()
            
        # Delivery questions
        elif any(keyword in message for keyword in ['delivery', 'shipping', 'when will it arrive']):
            return self.handle_delivery_questions()
            
        # General help
        elif any(keyword in message for keyword in ['help', 'support', 'contact']):
            return self.handle_help_questions()
            
        # Default response
        else:
            return self.default_response()
    
    def handle_order_status(self):
        orders = Order.objects.filter(user=self.user).order_by('-created_at')[:3]
        
        if not orders.exists():
            return "You don't have any recent orders. Would you like help finding products?"
            
        response = "Here are your recent orders:\n\n"
        for order in orders:
            response += f"• Order #{order.id} - {order.get_status_display()}\n"
            response += f"  Placed on: {order.created_at.strftime('%b %d, %Y')}\n"
            response += f"  Total: ₹{order.total_price}\n"
            response += f"  Track here: <a href='/orders/track/{order.id}/'>Track Order</a>\n\n"
        
        response += "You can view all orders in your account dashboard."
        return response
    
    def handle_prime_question(self):
        return """SentiMart Prime is our premium membership program that offers:
        
• Free fast delivery on all orders
• Early access to sales and deals
• Exclusive Prime-only discounts
• 5% cashback on all purchases

Would you like to learn more about Prime benefits?"""
    
    def handle_payment_questions(self):
        return """For payment-related questions:

• We accept credit/debit cards, UPI, net banking, and wallet payments
• Refunds are processed within 3-5 business days
• You can view payment options at checkout

For specific payment issues, please contact our support team."""
    
    def handle_delivery_questions(self):
        return """Our standard delivery takes 3-7 business days. 

For Prime members:
• Free 2-day delivery on most items
• Same-day delivery available in select cities

You can check estimated delivery dates on the product page or your order details."""
    
    def handle_help_questions(self):
        return """You can contact our customer support:
        
• Phone: 1800-123-4567 (24/7)
• Email: support@sentimart.com
• Live Chat: Available 8AM-10PM

What specific help do you need?"""
    
    def default_response(self):
        return """I'm sorry, I didn't understand that. Here are some things I can help with:
        
• Track your order status
• Explain SentiMart Prime benefits
• Answer delivery questions
• Help with payments

What would you like to know?"""