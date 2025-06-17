from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('seller', 'Seller'),
        ('buyer', 'Buyer'),
        ('delivery_agent', 'Delivery Agent')
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='buyer')
