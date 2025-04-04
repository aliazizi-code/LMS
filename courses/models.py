from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey

from utils import get_upload_to, validate_image_size, get_discounted_price, AutoSlugField


def get_upload_path(instance, filename):
    return get_upload_to(instance, filename, prefix='Course/banner')


class LearningLevel(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_('نام سطح آموزشی'))
    level_number = models.PositiveSmallIntegerField(unique=True, verbose_name=_('شماره سطح آموزشی'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))
    
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('سطح آموزشی')
        verbose_name_plural = _('سطوح آموزشی')
        ordering = ['level_number']
        unique_together = (('name', 'level_number'),)


class LearningPath(models.Model):
    start_level = models.ForeignKey(
        LearningLevel, related_name='learning_paths',
        on_delete=models.CASCADE, verbose_name=_('شروع سطح آموزشی')
    )
    end_level = models.ForeignKey(
        LearningLevel, related_name='learning_paths_end',
        on_delete=models.CASCADE, verbose_name=_('پایان سطح آموزشی')
    )
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    def clean(self):
        if self.start_level.level_number >= self.end_level.level_number:
            raise ValidationError(_('سطح شروع باید کمتر از سطح پایان باشد.'))
    
    def __str__(self):
        return f'{self.start_level} - {self.end_level}'
    
    def title(self):
        return f'سطح از {self.start_level} تا {self.end_level}'
    
    class Meta:
        verbose_name = _('مسیر آموزشی')
        verbose_name_plural = _('مسیرهای آموزشی')
        ordering = ['start_level', 'end_level']
        unique_together = (('start_level', 'end_level'),)


class CourseCategory(MPTTModel):
    title = models.CharField(max_length=200, verbose_name=_('عنوان دسته بندی'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    slug = AutoSlugField(source_field='title', verbose_name=_('آدرس دسته بندی'))
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('دسته بندی والد')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('دسته بندی دوره')
        verbose_name_plural = _('دسته بندی های دوره')
        ordering = ['title']
        unique_together = (('title', 'slug'),)


class Course(models.Model):
    class STATUS(models.TextChoices):
        COMPLETED = 'تمام شده', _('تمام شده')
        IN_PROGRESS = 'در حال پیشرفت', _('در حال پیشرفت')
        UPCOMING = 'در حال انتظار', _('در حال انتظار')
        CANCELLED = 'کنسل شده', _('کنسل شده')
        ARCHIVED = 'بایگانی شده', _('بایگانی شده')

    title = models.CharField(max_length=200, verbose_name=_('عنوان دوره'))
    slug = AutoSlugField(source_field='title', verbose_name=_('آدرس دوره'))
    description = models.TextField(verbose_name=_('توضیحات'))
    short_description = models.TextField(verbose_name=_('توضیحات کوتاه'))
    category = models.ManyToManyField(
        CourseCategory, related_name='courses',
        verbose_name=_('دسته بندی دوره')
    )
    tags = TaggableManager(verbose_name=_('برچسب ها'), blank=True)
    # comments = models.ManyToManyField('Comment', blank=True)
    learning_path = models.ForeignKey(
        LearningPath, related_name='courses',
        on_delete=models.CASCADE, blank=True, null=True,
        verbose_name=_('سطح مسیر آموزشی')
    )
    banner = models.ImageField(
        upload_to=get_upload_path,
        validators=[validate_image_size],
        verbose_name=_('بنر دوره')
    )
    banner_thumbnail = ImageSpecField(
        source='banner',
        processors=[ResizeToFill(120, 120)],
        format='jpeg',
        options={'quality': 80},
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS.choices,
        default=STATUS.UPCOMING,
        verbose_name=_('وضعیت دوره')
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='courses',
        on_delete=models.CASCADE,
        verbose_name=_('مدرس دوره')
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        verbose_name=_('امتیاز')
    )
    count_students = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد دانشجویان'))
    count_lessons = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد درس ها'))
    course_duration = models.DurationField(
        default=timezone.timedelta(0),
        verbose_name=_('مدت زمان دوره')
    )
    count_comments = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد نظرات'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))
    start_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاریخ شروع دوره'))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاریخ پایان دوره'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))

    def clean(self):
        if self.pk is None:
            return

        if self.status == self.STATUS.UPCOMING:
            raise ValidationError("Existing courses cannot be set to 'Upcoming'.")

        if self.status != self.STATUS.UPCOMING and self.start_date:
            raise ValidationError("Start date must be empty if the status is not 'Upcoming'.")

        if self.status == self.STATUS.UPCOMING and not self.start_date:
            raise ValidationError("Start date must be provided if the status is 'Upcoming'.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created_at']
        verbose_name = _('دوره')
        verbose_name_plural = _('دوره ها')
        unique_together = (('title', 'slug'),)


class Price(models.Model):
    course = models.OneToOneField(
        Course,
        related_name='prices',
        on_delete=models.CASCADE,
        verbose_name=_('دوره')
    )
    main_price = models.PositiveIntegerField(verbose_name=_('قیمت اصلی'))
    discount_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('درصد تخفیف')
    )
    final_price = models.PositiveIntegerField(verbose_name=_('قیمت نهایی'))
    discount_expires_at = models.DateTimeField(verbose_name=_('تاریخ انقضای تخفیف'))

    def __str__(self):
        return f'price {self.course.title}: {self.main_price}'

    def save(self, *args, **kwargs):
        if timezone.now() < self.discount_expires_at:
            self.final_price = get_discounted_price(self.main_price, self.discount_percentage)
        else:
            self.final_price = self.main_price
            # todo: use celery for reset discount_percentage
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('قیمت')
        verbose_name_plural = _('قیمت ها')
        unique_together = (('course', 'main_price'),)


class Season(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('عنوان فصل'))
    slug = AutoSlugField(source_field='title', verbose_name=_('آدرس فصل'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    season_duration = models.DurationField(
        default=timezone.timedelta(0),
        verbose_name=_('مدت زمان فصل')
    )
    course = models.ForeignKey(
        Course,
        related_name='seasons',
        on_delete=models.CASCADE,
        verbose_name=_('دوره')
    )
    

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('فصل')
        verbose_name_plural = _('فصل ها')
        unique_together = (('title', 'slug'),)


class Lesson(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('عنوان درس'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    url_video = models.URLField(verbose_name=_('آدرس ویدیو'))
    url_files = models.URLField(blank=True, null=True, verbose_name=_('آدرس فایل ها'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    season = models.ForeignKey(
        Season,
        related_name='lessons',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('فصل')
    )
    course = models.ForeignKey(
        Course,
        related_name='lessons',
        on_delete=models.CASCADE,
        verbose_name=_('دوره')
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = _('درس')
        verbose_name_plural = _('درس ها')
