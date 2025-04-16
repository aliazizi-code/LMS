from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, MaxLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from taggit.managers import TaggableManager
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from mptt.models import MPTTModel, TreeForeignKey

from utils import get_upload_to, validate_image_size, AutoSlugField


def get_upload_path(instance, filename):
    return get_upload_to(instance, filename, prefix='Course/banner')


class LearningLevel(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_('نام سطح آموزشی'))
    level_number = models.PositiveSmallIntegerField(unique=True, verbose_name=_('شماره سطح آموزشی'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))
    
    
    def __str__(self):
        return f"{self.name} {self.level_number}"
    
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
        on_delete=models.CASCADE, verbose_name=_('پایان سطح آموزشی'),
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    def clean(self):
        if self.end_level and self.start_level.level_number >= self.end_level.level_number:
            raise ValidationError(_('سطح شروع باید کمتر از سطح پایان باشد.'))
    
    def __str__(self):
        return f'{self.start_level} - {self.end_level}'
    
    def title(self):
        if self.end_level:
            return f'سطح از {self.start_level.name} تا {self.end_level.name}'
        return f"سطح {self.start_level.name}"
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('مسیر آموزشی')
        verbose_name_plural = _('مسیرهای آموزشی')
        ordering = ['start_level', 'end_level']
        unique_together = (('start_level', 'end_level'),)


class CourseCategory(MPTTModel):
    title = models.CharField(max_length=200, verbose_name=_('عنوان دسته بندی'))
    slug = models.SlugField(max_length=250, verbose_name=_('آدرس دسته بندی'))
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
    
    def clean(self):
        if self.parent:
            level = self.parent.get_level() + 1
            if level > 2:
                raise ValidationError(_('حداکثر تعداد سطوح دسته بندی ۲ سطح می‌باشد.'))
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('دسته بندی دوره')
        verbose_name_plural = _('دسته بندی های دوره')
        ordering = ['title']
        unique_together = (('title', 'slug'),)
        indexes = [
            models.Index(fields=['slug'])
        ]


class Course(models.Model):
    class STATUS(models.TextChoices):
        COMPLETED = 'COMPLETED', _('تکمیل شده')
        IN_PROGRESS = 'IN_PROGRESS', _('در حال برگذاری')
        UPCOMING = 'UPCOMING', _('به زودی')
        CANCELLED = 'CANCELLED', _('کنسل شده')
    
    class LANGUAGE(models.TextChoices):
        FA = 'fa', _('فارسی')
        EN = 'en', _('انگلیسی')
        AZ = 'az', _('ترکی آذربایجانی')

    title = models.CharField(max_length=200, verbose_name=_('عنوان دوره'))
    slug = AutoSlugField(source_field='title',verbose_name=_('آدرس دوره'))
    sv = SearchVectorField(null=True, editable=False)
    description = models.TextField(verbose_name=_('توضیحات'))
    short_description = models.TextField(verbose_name=_('توضیحات کوتاه'))
    categories = models.ManyToManyField(
        CourseCategory, related_name='courses',
        verbose_name=_('دسته بندی دوره')
    )
    tags = TaggableManager(verbose_name=_('برچسب ها'))
    language = models.CharField(
        max_length=50,
        choices=LANGUAGE.choices,
        verbose_name=_("زبان دوره")
    )
    prerequisites = models.CharField(
        max_length=100,
        blank=True, null=True,
        verbose_name=_('پیش نیاز')
    )
    learning_path = models.ForeignKey(
        LearningPath, related_name='courses',
        on_delete=models.CASCADE,
        verbose_name=_('سطح مسیر آموزشی')
    )
    banner = models.ImageField(
        upload_to=get_upload_path,
        validators=[validate_image_size],
        verbose_name=_('بنر دوره')
    )
    banner_thumbnail = ImageSpecField(
        source='banner',
        format='JPEG',
        options={'quality': 80},
    )
    url_video = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("لینک ویدیو"),
        help_text=_("این فیلد برای ویدیوهای کوتاه و آشنایی با دوره یا معرفی استاد است.")
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS.choices,
        verbose_name=_('وضعیت دوره')
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='courses',
        on_delete=models.CASCADE,
        verbose_name=_('مدرس دوره')
    )
    count_students = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد دانشجویان'))
    count_lessons = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد درس ها'))
    duration = models.DurationField(
        default=timezone.timedelta(0),
        editable=False,
        verbose_name=_('مدت زمان دوره')
    )
    count_comments = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد نظرات'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    has_seasons = models.BooleanField(default=False, verbose_name=_('فصل بندی شده/نشده'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))
    start_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاریخ شروع دوره'))
    last_lesson_update = models.DateTimeField(null=True, blank=True, editable=False, verbose_name=_('تاریخ آخرین بروزرسانی جلسات'))
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name=_('تاریخ بروزرسانی'))
    published_at = models.DateTimeField(blank=True, null=True, editable=False, verbose_name=_('تاریخ انتشار'))
    
    def update_lesson_date(self):
        self.last_lesson_update = timezone.now()
        self.save(update_fields=['last_lesson_update'])

    def clean(self):
        errors = {}

        if self.status == self.STATUS.UPCOMING and not self.start_date:
            errors['start_date'] = "تاریخ شروع باید ارائه شود اگر وضعیت 'UPCOMING' است."

        if self.status != self.STATUS.UPCOMING and self.start_date:
            errors['start_date'] = "تاریخ شروع باید خالی باشد اگر وضعیت 'UPCOMING' نیست."
        
        if self.is_published:
            if self.pk:
                old_instance = Course.objects.get(pk=self.pk)
                if old_instance.is_deleted == False and self.is_deleted == True:
                    raise ValidationError(
                        "امکان حذف دوره‌های منتشر شده وجود ندارد."
                    )

        if errors:
            raise ValidationError(errors)

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
        indexes = [
            GinIndex(fields=['sv']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_deleted', 'is_published']),
        ]


class Feature(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='features', verbose_name=_('دوره'))
    title = models.CharField(max_length=100, verbose_name=_('عنوان'))
    description = models.TextField(validators=[MaxLengthValidator(300)], verbose_name=_('توضیحات'))
    order = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('ترتیب دوره'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        ordering = ['order', 'created_at', 'id']
        verbose_name = _('ویژگی')
        verbose_name_plural = _('ویژگی ها')
        
    def __str__(self):
        return f"{self.title} - {self.course.title}"


class FAQ(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='faqs', verbose_name=_('دوره'))
    question = models.CharField(max_length=255, verbose_name=_('سوال'))
    answer = models.TextField(verbose_name=_('پاسخ'))
    order = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('ترتیب دوره'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        ordering = ['order', 'created_at', 'id']
        verbose_name = _('سوال متداول')
        verbose_name_plural = _('سوالات متداول')
        
    def __str__(self):
        return f"{self.question[:30]}... - {self.course.title}"


class Price(models.Model):
    course = models.OneToOneField(
        Course,
        related_name='price',
        on_delete=models.CASCADE,
        verbose_name=_('دوره')
    )
    main_price = models.PositiveIntegerField(verbose_name=_('قیمت اصلی'))
    discount_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('درصد تخفیف')
    )
    final_price = models.PositiveIntegerField(editable=False, verbose_name=_('قیمت نهایی'))
    discount_expires_at = models.DateTimeField(blank=True, null=True,verbose_name=_('تاریخ انقضای تخفیف'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    def save(self, *args, **kwargs):
        self.final_price = self.main_price * (100 - self.discount_percentage) // 100

        if self.discount_expires_at and self.discount_expires_at < timezone.now():
            self.discount_percentage = 0
            self.final_price = self.main_price
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.course.title} - {self.final_price} تومان'

    class Meta:
        verbose_name = _('قیمت')
        verbose_name_plural = _('قیمت ها')


class Season(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('عنوان فصل'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    order = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('ترتیب دوره'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))
    duration = models.DurationField(
        default=timezone.timedelta(0),
        verbose_name=_('مدت زمان فصل')
    )
    course = models.ForeignKey(
        Course,
        related_name='seasons',
        on_delete=models.CASCADE,
        verbose_name=_('دوره')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))

    def clean(self):
        super().clean()
        
        if self.course.is_published:
            if self.pk:
                old_instance = Season.objects.get(pk=self.pk)
                if old_instance.is_deleted == False and self.is_deleted == True:
                    raise ValidationError(
                        "امکان حذف فصل برای دوره‌های منتشر شده وجود ندارد."
                    )
                if old_instance.is_published == True and self.is_published == False:
                    raise ValidationError(
                        "امکان تغییر وضعیت از انتشار به عدم انتشار فصل برای دوره‌های منتشر شده وجود ندارد."
                    )

    def __str__(self):
        return self.title
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order', 'created_at', 'id']
        verbose_name = _('فصل')
        verbose_name_plural = _('فصل ها')


class Lesson(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('عنوان درس'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    url_video = models.URLField(verbose_name=_('آدرس ویدیو'), unique=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('ترتیب دوره'))
    url_files = models.URLField(blank=True, null=True, unique=True, verbose_name=_('آدرس فایل ها'))
    is_published = models.BooleanField(default=False, verbose_name=_('وضعیت انتشار'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))
    season = models.ForeignKey(
        Season,
        related_name='lessons',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('فصل')
    )
    course = models.ForeignKey(
        Course,
        related_name='lessons',
        on_delete=models.CASCADE,
        verbose_name=_('دوره')
    )
    duration = models.DurationField(
        default=timezone.timedelta(0),
        verbose_name=_('مدت زمان فصل')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    def clean(self):
        super().clean()
        
        if self.course.is_published:
            if self.pk:
                old_instance = Lesson.objects.get(pk=self.pk)
                if old_instance.is_deleted == False and self.is_deleted == True:
                    raise ValidationError(
                        "امکان حذف جلسه برای دوره‌های منتشر شده وجود ندارد."
                    )
                if old_instance.is_published == True and self.is_published == False:
                    raise ValidationError(
                        "امکان تغییر وضعیت از انتشار به عدم انتشار جلسه برای دوره‌های منتشر شده وجود ندارد."
                    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.clean()
        self.course.update_lesson_date()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['order', 'created_at', 'id']
        verbose_name = _('درس')
        verbose_name_plural = _('درس ها')
