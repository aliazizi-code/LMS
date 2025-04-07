from django.db.models.signals import post_save
from django.contrib.postgres.search import SearchVector
from django.dispatch import receiver
from courses.models import CourseCategory, Course, Price


@receiver(post_save, sender=CourseCategory)
def update_active_status_of_descendants(sender, instance, **kwargs):
    descendants = instance.get_descendants(include_self=True)
    descendants.update(is_active=instance.is_active)


@receiver(post_save, sender=Course)
def create_price_for_course(sender, instance, created, **kwargs):
    if created:
        Price.objects.create(course=instance, main_price=0, final_price=0)


@receiver(post_save, sender=Course)
def update_search_vector(sender, instance, **kwargs):
    Course.objects.filter(
        id=instance.id
    ).update(
        sv=SearchVector('title', 'short_description')
    )
