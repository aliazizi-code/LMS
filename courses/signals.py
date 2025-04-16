from django.db.models.signals import post_save, pre_save, post_delete
from django.db.models import F
from django.contrib.postgres.search import SearchVector
from django.dispatch import receiver
from django.utils import timezone
from courses.models import CourseCategory, Course, Price, Lesson, Season

from utils import get_discounted_price, update_descendants_active_status


@receiver(post_save, sender=CourseCategory)
def update_course_category_status(sender, instance, **kwargs):
    update_descendants_active_status(instance)


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


@receiver(pre_save, sender=Season)
def update_urls_video_and_file_on_delete(sender, instance, **kwargs):
    if instance.pk:
        original_season = Season.objects.get(pk=instance.pk)
        if original_season.is_deleted != instance.is_deleted and instance.is_deleted:
            instance.title = f"{instance.title} del"


@receiver(pre_save, sender=Price)
def set_final_price(sender, instance, **kwargs):
    final_price = instance.main_price

    if instance.discount_percentage:
        final_price = get_discounted_price(instance.main_price, instance.discount_percentage)

    Price.objects.filter(id=instance.id).update(final_price=final_price)
    
    # TODO: Use Celery for handling time-limited discounts in the future


@receiver(post_save, sender=Lesson)
def increase_count_lesson(sender, instance, created, **kwargs):
    if created:
        Course.objects.filter(pk=instance.course.pk).update(
            count_lessons=F('count_lessons') + 1 
        )


@receiver(post_delete, sender=Lesson)
def decrease_count_lesson(sender, instance, **kwargs):
    Course.objects.filter(pk=instance.course.pk).update(
            count_lessons=F('count_lessons') - 1 
        )


@receiver(pre_save, sender=Course)
def set_published_at(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = Course.objects.get(pk=instance.pk)
        except Course.DoesNotExist:
            return

        if not previous.is_published and instance.is_published and instance.published_at is None:
            instance.published_at = timezone.now()


            