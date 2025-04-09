from django.db.models.signals import post_save, pre_save
from django.contrib.postgres.search import SearchVector
from django.dispatch import receiver
from courses.models import CourseCategory, Course, Price, Lesson

from utils import get_discounted_price


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


@receiver(pre_save, sender=Course)
def update_title_and_slug_on_delete(sender, instance, **kwargs):
    if instance.pk:
        original_course = Course.objects.get(pk=instance.pk)
        if original_course.is_deleted != instance.is_deleted and instance.is_deleted:
            instance.title = f"{instance.title} del"
            instance.slug = f"{instance.slug}-del"


@receiver(pre_save, sender=Lesson)
def update_urls_video_and_file_on_delete(sender, instance, **kwargs):
    if instance.pk:
        original_lesson = Lesson.objects.get(pk=instance.pk)
        if original_lesson.is_deleted != instance.is_deleted and instance.is_deleted:
            instance.video = f"{instance.url_video}-del"
            instance.file = f"{instance.url_files}-del"


@receiver(pre_save, sender=Price)
def set_final_price(sender, instance, **kwargs):
    final_price = instance.main_price

    if instance.discount_percentage:
        final_price = get_discounted_price(instance.main_price, instance.discount_percentage)

    Price.objects.filter(id=instance.id).update(final_price=final_price)
    
    # TODO: Use Celery for handling time-limited discounts in the future

