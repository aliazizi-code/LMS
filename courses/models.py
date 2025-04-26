from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, MaxLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from simple_history.models import HistoricalRecords
from imagekit.models import ImageSpecField
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey

from utils import get_upload_to, validate_image_size, AutoSlugField


# region Upload Patch

def get_upload_banner(instance, filename):
    model_name = 'Course'
    object_name = f"{instance.slug}-{instance.id}"
    folder_type = 'banner'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)


def get_upload_videos(instance, filename):
    model_name = 'Course'
    object_name = f"{instance.course.slug}-{instance.course.id}"
    folder_type = 'videos'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)


def get_upload_attachments(instance, filename):
    model_name = 'Course'
    object_name = f"{instance.course.slug}-{instance.course.id}"
    folder_type = 'attachments'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)

# endregion


# region Choice class

class RequestActionChoices(models.TextChoices):
        ADD = 'add', _('ایجاد')
        UPDATE = 'update', _('ویرایش')
        DELETE = 'delete', _('حذف')


class RequestTargetTypeChoices(models.TextChoices):
    LESSON = 'lesson', _('درس')
    FEATURE = 'feature', _('ویژگی')
    FAQ = 'faq', _('سوالات متداول')
    SEASON = 'season', _('فصل')
    COURSE = 'course', _('دوره')


class RequestStatusChoices(models.TextChoices):
    PENDING = 'pending', _('در حال بررسی')
    APPROVED = 'approved', _('تایید شده')
    REJECTED = 'rejected', _('رد شده')
    NEED_REVISION = 'need_revision', _('نیاز به اصلاح')
    DRAFT = 'draft', _('پیش نویس')


class CourseStatusChoices(models.TextChoices):
    COMPLETED = 'COMPLETED', _('تکمیل شده')
    IN_PROGRESS = 'IN_PROGRESS', _('در حال برگذاری')
    UPCOMING = 'UPCOMING', _('به زودی')
    CANCELLED = 'CANCELLED', _('لغو شده')
    
class CourseLanguageChoices(models.TextChoices):
    # FA = 'fa', _('فارسی')
    # EN = 'en', _('انگلیسی')
    AZ = 'az', _('ترکی آذربایجانی')

#endregion


# region Model

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
        LearningLevel, related_name='learning_paths_start',
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
    title = models.CharField(max_length=200, verbose_name=_('عنوان دوره'))
    slug = AutoSlugField(source_field='title',verbose_name=_('آدرس دوره'))
    sv = SearchVectorField(blank=True, null=True, editable=False)
    description = models.TextField(verbose_name=_('توضیحات'))
    short_description = models.TextField(verbose_name=_('توضیحات کوتاه'))
    categories = models.ManyToManyField(
        CourseCategory, related_name='courses',
        verbose_name=_('دسته بندی دوره')
    )
    tags = TaggableManager(verbose_name=_('برچسب ها'))
    language = models.CharField(
        max_length=50,
        choices=CourseLanguageChoices.choices,
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
        upload_to=get_upload_banner,
        validators=[validate_image_size],
        blank=True, null=True,
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
        choices=CourseStatusChoices.choices,
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
    count_comments = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد نظر ها'))
    duration = models.DurationField(
        default=timezone.timedelta(0),
        editable=False,
        verbose_name=_('مدت زمان دوره')
    )
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
        
        if self.is_published and self.pk:
            old_instance = Course.objects.get(pk=self.pk)
                
            TERMINAL_STATUSES = ['IN_PROGRESS', 'COMPLETED', 'CANCELLED']
            if old_instance.status in TERMINAL_STATUSES and self.status == 'UPCOMING':
                errors['status'] = _(f"تغییر وضعیت از '{old_instance.get_status_display()}' ==> 'به زودی' ممکن نیست.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['published_at', 'id']
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
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))
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
    is_deleted = models.BooleanField(default=False, verbose_name=_('وضعیت حذف'))
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
        self.clean()
        
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

    def __str__(self):
        return f"{self.title} - {self.course}"

    class Meta:
        ordering = ['order', 'created_at', 'id']
        verbose_name = _('فصل')
        verbose_name_plural = _('فصل ها')


class Lesson(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('عنوان درس'))
    url_video = models.URLField(verbose_name=_('آدرس ویدیو'), unique=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('ترتیب دوره'))
    url_attachment = models.URLField(blank=True, null=True, unique=True, verbose_name=_('آدرس فایل ها'))
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
    published_at = models.DateTimeField(blank=True, null=True, editable=False, verbose_name=_('تاریخ انتشار'))
    
    def clean(self):
        super().clean()
        errors = {}

        if self.pk and self.season and self.season.course != self.course:
            errors['season'] = _(
                "فصل انتخاب شده با دوره انتخاب شده یکسان نیست. "
            )
            errors['course'] = _(
                "دوره انتخاب شده با فصل انتخاب شده یکسان نیست. "
            )

        if errors:
            raise ValidationError(errors)


    def __str__(self):
        return f"{self.title} - {self.course}"

    def save(self, *args, **kwargs):
        self.clean()
        self.course.update_lesson_date()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['order', 'published_at', 'id']
        verbose_name = _('درس')
        verbose_name_plural = _('درس ها')


class LessonMedia(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='media',
    )
    video = models.FileField(upload_to=get_upload_videos, blank=True, null=True)
    attachment = models.FileField(upload_to=get_upload_attachments, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        super().clean()
        errors = {}
        
        if not self.video and not self.attachment:
            error_msg = _("حداقل یکی از فیلدهای 'ویدیو' یا 'پیوست' باید مقدار داشته باشد.")
            errors['video'] = error_msg
            errors['attachment'] = error_msg
        
        if errors:
            raise ValidationError(errors)
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Media for {self.course}"
    
    class Meta:
        verbose_name = _("رسانه‌ی درس")
        verbose_name_plural = _("رسانه‌های درس")


class CourseRequest(models.Model): 
    target_type = models.CharField(max_length=20, choices=RequestTargetTypeChoices.choices)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=RequestActionChoices.choices)
    status = models.CharField(
        max_length=20, choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.DRAFT,
    )
    data = models.JSONField()
    history = HistoricalRecords()
    comments = models.TextField(null=True, blank=True)
    admin_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    need_revision = models.BooleanField(default=False)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_requests'
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name='admin_course_requests'
    )
    
    def clean(self):
        super().clean()
        errors = {}
        
        error_message = _("یافت نشد.")
        
        model_mapping = {
            RequestTargetTypeChoices.COURSE: (Course, 'teacher'),
            RequestTargetTypeChoices.SEASON: (Season, 'course__teacher'),
            RequestTargetTypeChoices.LESSON: (Lesson, 'course__teacher'),
            RequestTargetTypeChoices.FAQ: (FAQ, 'course__teacher'),
            RequestTargetTypeChoices.FEATURE: (Feature, 'course__teacher'),
        }
        
        if self.action != RequestActionChoices.ADD and self.target_type in model_mapping:
            ModelClass, teacher_field = model_mapping[self.target_type]
            filter_kwargs = {
                'pk': self.target_id,
                'is_deleted': False,
            }
            filter_kwargs[teacher_field] = self.teacher

            if not ModelClass.objects.filter(**filter_kwargs).exists():
                errors['target_id'] = error_message
        
        if self.status == RequestStatusChoices.NEED_REVISION and (not self.admin_response or self.admin_response == ''):
            errors['admin_response'] = _("در وضعیت نیاز به اصلاح باید پاسخی به مدرس داده شود.")
            
        if self.action == RequestActionChoices.DELETE and (not self.comments or self.comments == ''):
            errors['comments'] = _("برای درخواست از نوع حذف باید توضیحات درج شود.")
            
        if self.action != RequestActionChoices.ADD and not self.target_id:
            errors['target_id'] = _("نباید خالی باشد.")

        if errors:
            raise ValidationError(errors)
        
    def save(self, *args, **kwargs):
        self.clean()
        
        if self.status == RequestStatusChoices.NEED_REVISION:
            self.need_revision = True
        
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"CourseRequest(id={self.pk}, action={self.action}, status={self.status})"

    class Meta:
        verbose_name = _("درخواست")
        verbose_name_plural = _("درخواست ها")
        ordering = ['-created_at', '-id']

# endregion
