from autoslug import AutoSlugField
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from taggit.managers import TaggableManager

from accounts.models import User
from utils import get_upload_to, validate_image_size, get_discounted_price


def get_upload_path(instance, filename):
    return get_upload_to(instance, filename, prefix='Course/banner')


class Course(models.Model):
    class STATUS(models.TextChoices):
        COMPLETED = 'completed', _('Completed')
        IN_PROGRESS = 'in_progress', _('In Progress')
        UPCOMING = 'upcoming', _('Upcoming')

    title = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='title')
    description = models.TextField()
    tags = TaggableManager()
    # comments = models.ManyToManyField('Comment', blank=True)
    banner = models.ImageField(upload_to=get_upload_path, validators=[validate_image_size])
    banner_thumbnail = ImageSpecField(
        source='banner',
        processors=[ResizeToFill(120, 120)],
        format='jpg',
        options={'quality': 80}
    )
    status = models.CharField(max_length=20, choices=STATUS.choices, default=STATUS.UPCOMING)
    Teacher = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='courses', on_delete=models.CASCADE)
    count_students = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        unique_together = (('title', 'slug'),)


class Price(models.Model):
    course = models.OneToOneField(Course, related_name='prices', on_delete=models.CASCADE)
    main_price = models.PositiveIntegerField()
    discount_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    final_price = models.PositiveIntegerField()
    discount_expires_at = models.DateTimeField()

    def __str__(self):
        return f'price {self.course.title}: {self.main_price}'

    def save(self, *args, **kwargs):
        if timezone.now() < self.discount_expires_at:
            self.final_price = get_discounted_price(self.main_price, self.discount_percentage)
            # todo: use celery for reset discount_percentage
        super().save(*args, **kwargs)


class Season(models.Model):
    title = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='title')
    course = models.ForeignKey(Course, related_name='seasons', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')
        unique_together = (('title', 'slug'),)


class Video(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    url_video = models.URLField()
    url_files = models.URLField(blank=True, null=True)
    season = models.ForeignKey(Season, related_name='videos', on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, related_name='videos', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('Video')
        verbose_name_plural = _('Videos')
