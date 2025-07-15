from products.models import Order
from django.conf import settings
import openai
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Configure APIs
openai.api_key = settings.OPENAI_API_KEY
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Try initializing Gemini model
try:
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    gemini_available = True
except Exception as e:
    print("Gemini initialization failed:", e)
    gemini_available = False


class ChatbotEngine:
    def __init__(self, user):
        self.user = user
        self.gemini_chat = None

        if gemini_available:
            try:
                self.gemini_chat = model.start_chat(history=[])
                print("Gemini chat session started")
            except Exception as e:
                print(f"Failed to start Gemini chat: {e}")
                self.gemini_chat = None

    def process_message(self, message):
        msg_lower = message.lower().strip()

        # Specialized responses
        if any(q in msg_lower for q in ['track order', 'order status']):
            return self.handle_order_status()
        elif 'prime' in msg_lower or 'membership' in msg_lower:
            return self.handle_prime_question()
        elif any(q in msg_lower for q in ['payment', 'refund']):
            return self.handle_payment_questions()
        elif any(q in msg_lower for q in ['delivery', 'shipping']):
            return self.handle_delivery_questions()

      
        if self.gemini_chat:
            try:
                return self.handle_with_gemini(message)
            except Exception as e:
                print(f"Gemini failed, falling back to OpenAI: {e}")

      
        return self.handle_with_openai(message)

    def handle_with_gemini(self, message):
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

    def handle_with_openai(self, message):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or gpt-4 if enabled
                messages=[
                    {"role": "system", "content": (
                        "You are SentiMart's e-commerce assistant. Be concise (1-2 sentences), mention product categories "
                        "when relevant, suggest browsing the catalog, and never say 'I can help with...'."
                    )},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return self._sanitize_response(response.choices[0].message.content)

        except Exception as e:
            print(f"OpenAI error: {e}")
            return self.default_response()

    def _sanitize_response(self, text):
        return text.replace('**', '').replace('*', '').replace('](', ' (').replace('[', '')

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
