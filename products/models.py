from django.db import models
from django.conf import settings
from categories.models import Category
from delivery_agent.models import DeliveryAgent
from buyer.models import Address
# Create your models here.
# products/models.py

class Product(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='products', null=True)
    sub_category = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    brand_name = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(null=True, blank=True) 
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):

        return self.name

    def final_price(self):
        return self.base_price - self.discount

    def saved_amount(self):
        return self.discount

    def discount_percentage(self):
        if self.base_price > 0:
            return (self.discount / self.base_price) * 100
        return 0
    
class ProductAttribute(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    attributes = models.ManyToManyField(ProductAttributeValue)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {' - '.join([str(a) for a in self.attributes.all()])}"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product.final_price() * self.quantity

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('About to Deliver', 'About to Deliver'),
        ('Delivered', 'Delivered'),
        ('Rejected', 'Rejected'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_assigned = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(DeliveryAgent, null=True, blank=True, on_delete=models.SET_NULL)
    issue_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}x"



class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1)
    comment = models.TextField(blank=True)
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    invoice_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_id