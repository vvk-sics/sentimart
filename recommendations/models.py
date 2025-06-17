from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from products.models import Product

class UserProductInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    view_count = models.PositiveIntegerField(default=0)
    purchased = models.BooleanField(default=False)
    rating = models.PositiveIntegerField(null=True, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"