from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation.trans_null import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from mptt.models import MPTTModel, TreeForeignKey

from .managers import UserManager
from utils import validate_image_size, get_upload_to, PhoneNumberField


def avatar_get_upload_to(instance, filename):
    return get_upload_to(instance, filename, "users/avatar")


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Email Address')
    )
    phone = PhoneNumberField(verbose_name=_('Phone Number'))
    email_verify_token = models.SlugField(
        max_length=72,
        blank=True,
        null=True,
        verbose_name=_('Email Verify Token')
    )
    first_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('First name')
    )
    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Last name')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )
    is_admin = models.BooleanField(
        default=False,
        verbose_name=_('Admin Status')
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('Staff Status')
    )
    permissions = models.CharField(
        max_length=255,
        default='',
        blank=True,
        null=True,
        verbose_name=_('User Permissions')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Account Creation Date')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Update Date')
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
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
    title = models.CharField(max_length=200)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Job Category'
        verbose_name_plural = 'Job Categories'
        ordering = ['title']


class Job(models.Model):
    title = models.CharField(max_length=200)
    category = models.ManyToManyField(JobCategory, related_name='jobs')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['title']


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        male = 'M', _('Male')
        female = 'F', _('Female')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profiles'
    )
    bio = models.TextField(
        blank=True,
        null=True
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='profiles',
        blank=True,
        null=True
    )
    avatar = models.ImageField(
        upload_to=avatar_get_upload_to,
        validators=[validate_image_size],
        blank=True,
        null=True
    )
    avatar_thumbnail = ImageSpecField(
        source='avatar',
        processors=[ResizeToFill(120, 120)],
        format='jpg',
        options={'quality': 80}
    )
    age = models.PositiveSmallIntegerField(
        blank=True,
        null=True
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('Users Profile')
        ordering = ['-id']
        db_table = 'user_profile'

    def __str__(self):
        return str(self.user)
