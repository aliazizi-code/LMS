from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation.trans_null import gettext_lazy as _
from django.core.exceptions import ValidationError
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager

from .managers import UserManager
from utils import validate_image_size, get_upload_to, PhoneNumberField


def avatar_get_upload_to(instance, filename):
    return get_upload_to(instance, filename, "users/avatar")


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('آدرس ایمیل')
    )
    phone = PhoneNumberField(verbose_name=_('شماره موبایل'))
    email_verify_token = models.SlugField(
        max_length=72,
        blank=True,
        null=True,
        verbose_name=_('کد تایید ایمیل')
    )
    first_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('نام')
    )
    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('نام خانوادگی')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('وضعیت فعال بودن/نبودن')
    )
    is_admin = models.BooleanField(
        default=False,
        verbose_name=_('ادمین بودن/نبودن')
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('وضعیت کارمند بودن/نبودن')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاریخ ثبت نام')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاریخ ویرایش')
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('کاربر')
        verbose_name_plural = _('کاربران')
        ordering = ['created_at']
        db_table = 'custom_user'

    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"
        return ""

    def __str__(self):
        full_name = self.full_name()
        return f"{full_name.strip()} ({self.phone or self.email})".strip()


class JobCategory(MPTTModel):
    title = models.CharField(max_length=200, verbose_name=_('عنوان'))
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('والد')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('وضعیت فعال بودن/نبودن'))

    def __str__(self):
        return self.title
    
    def clean(self):
        if self.parent:
            level = self.parent.get_level() + 1
            if level > 2:
                raise ValidationError(_('حداکثر تعداد سطوح دسته بندی ۲ سطح می‌باشد.'))

    class Meta:
        verbose_name = _('دسته بندی شغل')
        verbose_name_plural = _('دسته بندی شغل ها')
        ordering = ['title']


class Job(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('عنوان'))
    category = models.ManyToManyField(JobCategory, related_name='jobs', verbose_name=_('دسته بندی'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('شغل')
        verbose_name_plural = _('شغل ها')
        ordering = ['title']


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        male = 'M', _('مرد')
        female = 'F', _('زن')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profiles',
        verbose_name=_('کاربر')
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('بیوگرافی')
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='profiles',
        blank=True,
        null=True,
        verbose_name=_('شغل')
    )
    avatar = models.ImageField(
        upload_to=avatar_get_upload_to,
        validators=[validate_image_size],
        blank=True,
        null=True,
        verbose_name=_('عکس پروفایل')
    )
    avatar_thumbnail = ImageSpecField(
        source='avatar',
        processors=[ResizeToFill(120, 120)],
        format='jpg',
        options={'quality': 80}
    )
    age = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_('سن')
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        blank=True,
        null=True,
        verbose_name=_('جنسیت')
    )

    class Meta:
        verbose_name = _('پروفایل کاربر')
        verbose_name_plural = _('پروفایل کاربران')
        ordering = ['-id']
        db_table = 'user_profile'

    def __str__(self):
        return str(self.user)


class SocialLink(models.Model):
    class SocialMediaType(models.TextChoices):
        telegram = 'telegram', _('تلگرام')
        instagram = 'instagram', _('اینستاگرام')
        linkedin = 'linkedin', _('لینکدین')
        x = 'x', _('ایکس')
        threads = 'threads', _('تردز')
        facebook = 'facebook', _('فیسبوک')
        youtube = 'youtube', _('یوتیوب')
        github = 'github', _('گیت‌هاب')
        gitlab = 'gitlab', _('گیت‌لب')
    
    social_media_type = models.CharField(
        max_length=20,
        choices=SocialMediaType.choices,
        verbose_name=_('نوع شبکه اجتماعی'),
    )
    url = models.URLField(
        unique=True,
        verbose_name=_('آدرس'),
    )
    employee_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='social_links',
        verbose_name=_('پروفایل کارمند'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاریخ ثبت نام')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاریخ ویرایش')
    )
    
    def __str__(self):
        return self.title
    
    def clean(self):
        pass
        
    
    class Meta:
        verbose_name = _('لینک اجتماعی')
        verbose_name_plural = _('لینک های اجتماعی')
        ordering = ['employee_profile', 'id']
        permissions = (
            ("can_teacher", "Can teacher"),
            ("can_employee", "Can employee"),
            # ("can_author", "Can author"),
        )


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name=_('کاربر')
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_('نام کاربری'),
    )
    skills = TaggableManager(
        blank=True,
        verbose_name=_('مهارت ها'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاریخ ثبت نام')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاریخ ویرایش')
    )
    
    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = _('پروفایل کارمند')
        verbose_name_plural = _('پروفایل کارمندان')
        permissions = (
            ("can_teacher", "Can teacher"),
            ("can_employee", "Can employee"),
            # ("can_author", "Can author"),
        )
