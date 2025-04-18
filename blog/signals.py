from utils import update_descendants_active_status
from .models import ArticleCategory
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=ArticleCategory)
def update_article_category_status(sender, instance, **kwargs):
    update_descendants_active_status(instance)
