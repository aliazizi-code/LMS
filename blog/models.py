from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from autoslug import AutoSlugField
from django.utils.translation.trans_null import gettext_lazy as _
from taggit.managers import TaggableManager
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.conf import settings
from utils import get_upload_to, validate_image_size, AutoSlugField
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.contrib.postgres.search import SearchVectorField


def get_upload_banner(instance, filename):
    model_name = 'Article'
    object_name = f"{instance.slug}-{instance.id}"
    folder_type = 'banner'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)


def get_upload_images(instance, filename):
    model_name = 'Article'
    object_name = f"{instance.article.slug}-{instance.article.id}"
    folder_type = 'images'
    return get_upload_to(instance, filename, model_name, object_name, folder_type)


class RequestStatusChoices(models.TextChoices):
    PENDING = 'pending', _('در حال بررسی')
    APPROVED = 'approved', _('تایید شده')
    REJECTED = 'rejected', _('رد شده')
    NEED_REVISION = 'need_revision', _('نیاز به اصلاح')
    DRAFT = 'draft', _('پیش نویس')


class RequestActionChoices(models.TextChoices):
        ADD = 'add', _('انتشار')
        UPDATE = 'update', _('ویرایش')
        DELETE = 'delete', _('حذف')


class ArticleCategory(MPTTModel):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(source_field='name')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='childrens')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Article Category')
        verbose_name_plural = _('Article Categories')
        ordering = ['name']
        db_table = 'article_category'

    class MPTTMeta:
        order_insertion_by = ['name']
    
    def __str__(self):
        return self.name
    
    
class Article(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=250)
    slug = AutoSlugField(source_field='title')
    sv = SearchVectorField(blank=True, null=True, editable=False)
    banner = models.ImageField(
        upload_to=get_upload_banner,
        validators=[validate_image_size],

    )
    banner_thumbnail = ImageSpecField(
        source='banner',
        processors=[ResizeToFill(120, 120)],
        format='JPEG',
        options={'quality': 80}
    ) 
    category = models.ManyToManyField(ArticleCategory, related_name="articles", db_table='article_category_link')
    content = models.models.JSONField()
    is_published = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        ordering = ['-created_at']
        db_table = 'article'

    def __str__(self):
        return self.title


class ArticleRequest(models.Model):
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
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_requests'
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        editable=False,
        related_name='admin_article_requests'
    )


class ArticleImage(models.Model):
    image = models.ImageField(upload_to=get_upload_banner, validators=[validate_image_size])
    alt_text = models.CharField(max_length=255)
