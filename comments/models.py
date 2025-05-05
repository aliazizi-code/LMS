from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey
from simple_history.models import HistoricalRecords


class Comment(MPTTModel):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("نوع محتوا")
    )
    object_slug = models.CharField(max_length=255, verbose_name=_("اسلاگ شی"))
    content_object = GenericForeignKey(ct_field="content_type", fk_field="object_slug")
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name=_('کاربر')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='approved_by_comments',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('تایید شده توسط')
    )
    text = models.TextField(verbose_name=_("متن نظر"))
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies',
        verbose_name=_('والد')
    )
    history = HistoricalRecords(excluded_fields=['lft', 'rght', 'tree_id', 'level'])
    is_approved = models.BooleanField(default=False, verbose_name=_("تایید شده"))
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ تایید"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاریخ بروزرسانی"))
    
    def __str__(self):
        if len(self.text) > 80:
            return f"{self.text[:80]}..."
        else:
            return f"{self.text}"
        
    def clean(self):
        super().clean()
        
        ALLOWED_COMMENT_MODELS = ["article", "course"]
        
        if self.content_type and self.object_slug:
            related_model = self.content_type.model_class()
            
            if related_model._meta.model_name.lower() not in ALLOWED_COMMENT_MODELS:
                raise ValidationError(_("این مدل اجازه‌ی دریافت کامنت را ندارد."))
            
            if not related_model.objects.filter(
                slug=self.object_slug, is_published=True,
                is_deleted=False).exists():
                raise ValidationError(
                    _("شی مرتبط با این اسلاگ در مدل وجود ندارد.")
                )
        
        if self.parent is not None:
            if not self.parent.is_approved:
                raise ValidationError(
                    _("فقط می‌توان به کامنت‌های تأیید شده پاسخ داد.")
                )
            
            if self.parent.object_slug != self.object_slug:
                raise ValidationError(
                    _("اسلاگ ها باید برابر باشد.")
                )

            if self.parent.parent is not None:
                raise ValidationError(
                    _("امکان پاسخ به یک پاسخ دیگر وجود ندارد. فقط یک سطح پاسخ مجاز است.")
                )
          
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class MPTTMeta:
        order_insertion_by = ['created_at']

    class Meta:
        verbose_name = _("نظر")
        verbose_name_plural = _("نظرات")
