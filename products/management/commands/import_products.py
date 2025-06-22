import requests
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Product, Category, ProductAttribute, ProductAttributeValue, ProductVariant
import os
from urllib.parse import urlparse
from django.core.files import File
from urllib.request import urlretrieve
from tempfile import NamedTemporaryFile
from django.utils.text import slugify

User = get_user_model()


def download_image_from_url(image_url, product_name):
    """
    Download image from URL and return a Django File object
    """
    try:
        # Create a temporary file
        img_temp = NamedTemporaryFile(delete=True)
        
        # Download the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        # Write the image data to the temporary file
        for block in response.iter_content(1024 * 8):
            if not block:
                break
            img_temp.write(block)
        
        img_temp.flush()
        
        # Get the filename from URL or generate one
        filename = os.path.basename(urlparse(image_url).path)
        if not filename:
            filename = f"{slugify(product_name)}.jpg"
        
        return File(img_temp, name=filename)
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None
    

class Command(BaseCommand):
    help = 'Import products from FakeStoreAPI with proper image handling'

    def handle(self, *args, **options):
        # Get or create admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
        
        # Create categories and products
        response = requests.get('https://fakestoreapi.com/products')
        products = response.json()
        
        for api_product in products[:10]:  # First 10 products
            try:
                # Get or create category
                category, _ = Category.objects.get_or_create(
                    name=api_product['category'].title(),
                    slug=slugify(api_product['category'])
                )
                
                # Download and prepare image
                image_file = download_image_from_url(
                    api_product['image'],
                    api_product['title']
                )
                
                # Create product
                product = Product.objects.create(
                    seller=admin_user,
                    name=api_product['title'][:200],
                    description=api_product.get('description', 'No description')[:500],
                    base_price=api_product['price'],
                    discount=0,
                    category=category,
                    status='approved',
                    image=image_file  # This now uses the properly downloaded file
                )
                
                # Create variants (simplified example)
                color_attr, _ = ProductAttribute.objects.get_or_create(name='Color')
                color_val, _ = ProductAttributeValue.objects.get_or_create(
                    attribute=color_attr,
                    value='Default'
                )
                
                ProductVariant.objects.create(
                    product=product,
                    price=api_product['price'],
                    stock=10,
                ).attributes.add(color_val)
                
                self.stdout.write(self.style.SUCCESS(f"Created product: {product.name}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with {api_product['title']}: {str(e)}"))

