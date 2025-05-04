from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from django.db.models import F

from .models import ContentVisit


# @receiver(m2m_changed, sender=ContentVisit)
# def update_unique_views(sender, created, instance, **kwargs):
#     if created:
#         related_model = instance.content_type.model_class()
#         related_model.objects.filter(
#             slug=instance.object_slug,
#             is_deleted=False,
#             is_published=True,
#         ).update(
#             unique_views=F('unique_views') + 1
#         )
