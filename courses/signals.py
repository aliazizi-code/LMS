from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import CourseCategory


@receiver(post_save, sender=CourseCategory)
def update_active_status_of_descendants(sender, instance, **kwargs):
    descendants = instance.get_descendants(include_self=True)
    descendants.update(is_active=instance.is_active)
