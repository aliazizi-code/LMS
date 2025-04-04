from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from autoslug import AutoSlugField
from django.utils.translation.trans_null import gettext_lazy as _


class ArticleCategory(MPTTModel):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from=name, unique=True)
    description = models.TextField()
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = _('Article Category')
        verbose_name_plural = _('Article Categories')
        ordering = ['name']
        db_table = 'article_categories'

    class MPTTMeta:
        order_insertion_by = ['name']
    
