from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class ContentVisit(models.Model):
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name=_("نوع محتوا")
    )
    object_slug = models.CharField(max_length=255, verbose_name=_("اسلاگ شی"))
    content_object = GenericForeignKey(ct_field="content_type", fk_field="object_slug")
    
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"بازدید {self.content_type} ({self.object_slug}) - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def clean(self):
        super().clean()
        
        ALLOWED_VISIT_MODELS = ["article", "course"]
        
        if self.content_type and self.object_slug:
            related_model = self.content_type.model_class()
            
            if related_model._meta.model_name.lower() not in ALLOWED_VISIT_MODELS:
                raise ValidationError(_("این مدل اجازه‌ی دریافت بازدید را ندارد."))
    
    class Meta:
        verbose_name = _("بازدید محتوا")
        verbose_name_plural = _("بازدیدهای محتوا") 
        unique_together = ('content_type', 'object_slug', 'session_key')
        indexes = [
            models.Index(fields=['content_type', 'object_slug', 'session_key']),
        ]
