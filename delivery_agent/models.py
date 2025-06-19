from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
# Create your models here.

class DeliveryAgent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_agent_profile', null=True)
    phone = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    own_vehicle = models.BooleanField(default=False)
    licence_number = models.CharField(max_length=100)
    licence_expiry_date = models.DateField()
    driving_licence = models.ImageField(upload_to='driving_licences/')
    login_streak = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)
    total_ratings = models.PositiveIntegerField(default=0)
    rating_sum = models.FloatField(default=0)
    average_rating = models.FloatField(default=4.5)

    def __str__(self):
        return self.user.username
    
    def update_login_streak(self):
        today = timezone.now().date()
        if not self.last_login_date:
            self.login_streak = 1
        elif self.last_login_date == today - timedelta(days=1):
            self.login_streak += 1
        elif self.last_login_date != today:
            self.login_streak = 1
        self.last_login_date = today
        self.save()
    
    def update_rating(self):
        from products.models import Order
        ratings = Order.objects.filter(
            assigned_to=self,
            status='Delivered'
        ).exclude(delivery_rating__isnull=True)
        
        self.total_ratings = ratings.count()
        self.rating_sum = sum(r.delivery_rating for r in ratings if r.delivery_rating is not None)
        self.average_rating = round(self.rating_sum / self.total_ratings, 1) if self.total_ratings > 0 else 4.5
        self.save()

class OrderVisibility(models.Model):
    order = models.ForeignKey('products.Order', on_delete=models.CASCADE)
    agent = models.ForeignKey(DeliveryAgent, on_delete=models.CASCADE)
    rejected = models.BooleanField(default=False)

    class Meta:
        unique_together = ('order', 'agent')