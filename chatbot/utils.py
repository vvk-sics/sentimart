# chatbot/utils.py
from products.models import Order
from django.utils import timezone
from django.conf import settings
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Configure Gemini
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    
    # Use one of the actually available models from your console output
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    
    # Test the connection
    test_response = model.generate_content("Test connection").text
    print(f"✅ Gemini initialized successfully. Test response: {test_response}")
    
except Exception as e:
    print(f"❌ Gemini initialization failed: {e}")
    model = None

class ChatbotEngine:
    def __init__(self, user):
        self.user = user
        if model:
            try:
                self.gemini_chat = model.start_chat(history=[])
                print("Chat session started with Gemini")
            except Exception as e:
                print(f"Failed to start chat: {e}")
                self.gemini_chat = None
        else:
            self.gemini_chat = None
    
    def process_message(self, message):
        msg_lower = message.lower().strip()
        
        # Specialized handlers (unchanged)
        if any(q in msg_lower for q in ['track order', 'order status']):
            return self.handle_order_status()
        elif 'prime' in msg_lower or 'membership' in msg_lower:
            return self.handle_prime_question()
        elif any(q in msg_lower for q in ['payment', 'refund']):
            return self.handle_payment_questions()
        elif any(q in msg_lower for q in ['delivery', 'shipping']):
            return self.handle_delivery_questions()
        
        # Try Gemini if available
        if self.gemini_chat:
            try:
                return self.handle_with_gemini(message)
            except Exception as e:
                print(f"Gemini processing error: {e}")
                return "Our product catalog has what you need! Visit our store to browse options."
                
        return self.default_response()
        
    def handle_with_gemini(self, message):
        try:
            response = self.gemini_chat.send_message(
                f"""You are SentiMart's e-commerce assistant. Respond to:
                Question: {message}
                
                Guidelines:
                - Be concise (1-2 sentences)
                - Mention product categories when relevant
                - For product questions, suggest browsing our catalog
                - Never say "I can help with..."
                """,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 150
                }
            )
            return self._sanitize_response(response.text)
            
        except google_exceptions.GoogleAPIError as e:
            print(f"Gemini API Error: {e}")
            return "Our product catalog has what you need! Visit our store to browse options."
        except Exception as e:
            print(f"Unexpected Gemini error: {e}")
            return self.default_response()
    
    def _sanitize_response(self, text):
        """Clean up Gemini responses for our chat interface"""
        # Remove markdown formatting if present
        clean_text = text.replace('**', '').replace('*', '')
        # Ensure URLs are properly formatted
        clean_text = clean_text.replace('](', ' (').replace('[', '')
        return clean_text
    
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
• Priority customer support

Would you like to learn more or sign up for Prime?"""
    
    def handle_payment_questions(self):
        return """For payment-related questions:

• We accept credit/debit cards, UPI, net banking, and wallet payments
• Refunds are processed within 3-5 business days
• Payment failures? Try again after 30 minutes
• You can view payment options at checkout

For specific payment issues, please visit our Payments Help Center."""

    def handle_delivery_questions(self):
        return """Our delivery options:

Standard Delivery: 3-7 business days (Free on orders ₹499+)
Express Delivery: 2-3 business days (₹99)
Prime Members: Free 2-day delivery on most items

You can check exact delivery dates during checkout."""

    def handle_help_questions(self):
        return """Contact SentiMart Support:

• Phone: 1800-123-4567 (24/7)
• Email: support@sentimart.com
• Live Chat: Available 8AM-10PM
• Help Center: <a href='/help/'>Visit Help Center</a>

What specific help do you need?"""
    
    def default_response(self):
        return """I'm here to help with your SentiMart experience. Here are things I can assist with:
        
• Track your order status
• Explain SentiMart Prime benefits
• Answer delivery questions
• Help with payments and refunds
• Product recommendations

What would you like to know?"""