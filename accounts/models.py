from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group
from django.utils.translation.trans_null import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from imagekit.models import ImageSpecField
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager

from .managers import UserManager
from utils import (
    validate_image_size,
    get_upload_to,
    PhoneNumberField,
    validate_persian,
)


def avatar_get_upload_to(instance, filename):
    return get_upload_to(instance.pk, filename, "users/avatar")


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
        verbose_name=_('نام'),
        validators=[validate_persian]
    )
    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('نام خانوادگی'),
        validators=[validate_persian]
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
        return "ناشناس"

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
        related_name='user_profile',
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
        related_name='user_profile',
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
        format='JPEG',
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
        indexes = [
            models.Index(fields=['age', 'gender', 'job']),
            models.Index(fields=['bio'], condition=Q(bio__isnull=False) & ~Q(bio=''), name='non_empty_bio_idx'),
        ]

    def __str__(self):
        return str(self.user)


class EmployeeProfileManager(models.Manager):
    def filter_completed_profiles(self):
        return self.get_queryset().select_related(
            'user_profile',
            'user_profile__user',
            'user_profile__job'
        ).filter(
            username__isnull=False,
            user_profile__user__first_name__isnull=False,
            user_profile__user__last_name__isnull=False,
            user_profile__age__isnull=False,
            user_profile__gender__isnull=False,
            user_profile__job__isnull=False,
            user_profile__bio__isnull=False,
        ).exclude(
            user_profile__bio=''
        ).only(
            'id', 'username', 'created_at',
            'user_profile__age',
            'user_profile__gender',
            'user_profile__bio',
            'user_profile__user__first_name',
            'user_profile__user__last_name',
            'user_profile__job__title'
        )


class EmployeeProfile(models.Model):
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name=_('پروفایل عمومی کاربر')
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_('نام کاربری'),
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9]{3,150}$',
                message=_('نام کاربری باید فقط شامل حروف کوچک انگلیسی و اعداد باشد و نباید فاصله یا علامت خاصی داشته باشد.')
            )
        ],
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
    
    objects = EmployeeProfileManager()
    
    def __str__(self):
        return str(self.user_profile.user)

    class Meta:
        verbose_name = _('پروفایل کارمند')
        verbose_name_plural = _('پروفایل کارمندان')
        permissions = (
            ("can_teacher", "Can teacher"),
            ("can_employee", "Can employee"),
            # ("can_author", "Can author"),
        )


class Position(models.Model):
    employee_profile = models.OneToOneField(
        EmployeeProfile,
        on_delete=models.CASCADE,
        verbose_name=_('پروفایل کارمند'),
        related_name='position'
    )
    roles = TaggableManager(
        blank=True,
        verbose_name=_("نقش های کارمند")
    )
    
    class Meta:
        verbose_name = _('موقعیت شغلی')
        verbose_name_plural = _('موقعیت‌های شغلی')
        


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
    link = models.URLField(
        unique=True,
        verbose_name=_('آدرس'),
    )
    employee_profile = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='social_link',
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
        return f"{self.employee_profile.username} - {self.social_media_type}"
    
    def clean(self):
        super().clean()
        count = SocialLink.objects.filter(employee_profile=self.employee_profile).count()
        if count >= 5:
            raise ValidationError(_('هر کاربر نمی‌تواند بیش از ۵ لینک اجتماعی ایجاد کند.'))
        
        patterns = {
            self.SocialMediaType.telegram: "https://t.me/",
            self.SocialMediaType.instagram: "https://www.instagram.com/",
            self.SocialMediaType.linkedin: "https://www.linkedin.com/",
            self.SocialMediaType.x: "https://x.com/",
            self.SocialMediaType.threads: "https://www.threads.net/",
            self.SocialMediaType.facebook: "https://www.facebook.com/",
            self.SocialMediaType.youtube: "https://www.youtube.com/",
            self.SocialMediaType.github: "https://github.com/",
            self.SocialMediaType.gitlab: "https://gitlab.com/",
        }

        if self.social_media_type in patterns and not self.link.startswith(patterns[self.social_media_type]):
            raise ValidationError(_(f'لینک {self.SocialMediaType(self.social_media_type).label} باید با "{patterns[self.social_media_type]}" شروع شود.'))
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = _('لینک اجتماعی')
        verbose_name_plural = _('لینک های اجتماعی')
        ordering = ['employee_profile', 'id']
        permissions = (
            ("can_teacher", "Can teacher"),
            ("can_employee", "Can employee"),
            # ("can_author", "Can author"),
        )


class CustomGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, verbose_name=_("گروه"), related_name='custom_group')
    description = models.TextField(null=True, blank=True, verbose_name=_("توضیحات"))
    is_display = models.BooleanField(default=False, verbose_name=_("وضعیت نمایش"))
    
    def __str__(self):
        return str(self.group)
    
    class Meta:
        verbose_name = _('گروه سفارشی')
        verbose_name_plural = _('گروه های سفارشی')
        ordering = ['group']
