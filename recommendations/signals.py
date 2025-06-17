from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from recommendations.models import UserProductInteraction
from products.models import OrderItem, Review

@receiver(post_save, sender=OrderItem)
def update_purchased_interaction(sender, instance, created, **kwargs):
    if created:
        interaction, created = UserProductInteraction.objects.get_or_create(
            user=instance.order.user,
            product=instance.product
        )
        interaction.purchased = True
        interaction.save()

@receiver(post_save, sender=Review)
def update_rating_interaction(sender, instance, created, **kwargs):
    interaction, created = UserProductInteraction.objects.get_or_create(
        user=instance.user,
        product=instance.product
    )
    interaction.rating = instance.rating
    interaction.save()