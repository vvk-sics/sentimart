import re
from products.models import Product, Order
from categories.models import Category

class ChatbotEngine:
    def __init__(self, user):
        self.user = user
    
    def process_message(self, message):
        message = message.lower().strip()
        
        # Order status queries
        if any(word in message for word in ['order', 'status', 'track']):
            return self.handle_order_status()
        
        # Product queries
        elif any(word in message for word in ['product', 'item', 'buy', 'purchase']):
            return self.handle_product_query(message)
        
        # Category queries
        elif any(word in message for word in ['category', 'categories', 'type']):
            return self.handle_category_query()
        
        # Default response
        else:
            return "I can help with:\n1. Order status\n2. Product information\n3. Category listings\n\nTry asking 'Where is my order?' or 'Show me smartphones'"

    def handle_order_status(self):
        orders = Order.objects.filter(user=self.user).order_by('-created_at')
        if not orders.exists():
            return "You don't have any orders yet."
        
        response = "Your recent orders:\n"
        for order in orders[:3]:  # Show last 3 orders
            items = ", ".join([item.product.name for item in order.items.all()[:3]])
            response += f"\nOrder #{order.id} ({order.status}): {items}"
            if order.items.count() > 3:
                response += f" and {order.items.count() - 3} more items"
        return response

    def handle_product_query(self, message):
        # Extract price range if mentioned
        price_match = re.search(r'under (\d+)', message)
        max_price = float(price_match.group(1)) if price_match else None
        
        # Extract category if mentioned
        category = None
        for cat in Category.objects.all():
            if cat.name.lower() in message:
                category = cat
                break
        
        # Build query
        products = Product.objects.filter(status='approved')
        if category:
            products = products.filter(category=category)
        if max_price:
            products = products.filter(final_price__lte=max_price)
        
        products = products.order_by('-created_at')[:5]  # Limit to 5 results
        
        if not products.exists():
            return "No products found matching your criteria."
        
        response = "Here are some products:\n"
        for product in products:
            response += f"\n{product.name} - ₹{product.final_price()} (Save ₹{product.saved_amount()})"
        return response

    def handle_category_query(self):
        categories = Category.objects.all()
        if not categories.exists():
            return "No categories available yet."
        
        return "Available categories:\n" + "\n".join([cat.name for cat in categories])