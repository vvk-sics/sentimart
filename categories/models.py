from django.db import models
from django.utils.text import slugify
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='categories/')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Replace apostrophes and other special chars
            self.slug = slugify(self.name.replace("'", ""))
        super().save(*args, **kwargs)