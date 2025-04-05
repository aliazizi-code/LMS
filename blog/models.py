from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from autoslug import AutoSlugField
from django.utils.translation.trans_null import gettext_lazy as _
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
from taggit.managers import TaggableManager
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.conf import settings
from utils import get_upload_to, validate_image_size, AutoSlugField


def get_upload_image(instance, filename):
    return get_upload_to(instance, filename, prefix='Article/image')


class ArticleCategory(MPTTModel):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(source_field='name')
    description = models.TextField()
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
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
    class STATUS(models.TextChoices):
        IN_REVIEW = '-در-حال-بررسی', _('در-حال-بررسی')
        PUBLISHED = 'منتشر-شده-است', _('منتشر-شده-است')
        NEEDS_CORRECTION = 'نیاز-به-اصلاح دارد', _('نیاز-به-اصلاح دارد')
        NOT_CONFIRMED = 'تایید-نشد', _('تایید-نشد')

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=250)
    slug = AutoSlugField(source_field='title')
    image = models.ImageField(
        upload_to=get_upload_image,
        validators=[validate_image_size],

    )
    # image_thumbnail need to fix
    image_thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(120, 120)],
        format='jpg',
        options={'quality': 80}
    ) 
    category = models.ManyToManyField(ArticleCategory, related_name="articles")
    content = MarkdownField(rendered_field='content_rendered', validator=VALIDATOR_STANDARD)
    content_rendered = RenderedMarkdownField() 
    short_description = models.TextField()
    tags = TaggableManager()
    status = models.CharField(
        max_length=30,
        choices=STATUS.choices,
        default=STATUS.IN_REVIEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        ordering = ['-created_at']
        db_table = 'article'
