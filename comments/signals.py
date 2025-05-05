from django.utils import timezone
from django.db.models.signals import pre_save, post_delete
from django.db.models import F
from django.dispatch import receiver
from .models import Comment


def update_comment_count(instance, increment=True):
    related_model = instance.content_type.model_class()
    if related_model:
        adjustment = 1 if increment else -1
        related_model.objects.filter(slug=instance.object_slug).update(
            count_comments=F('count_comments') + adjustment
        )


@receiver(pre_save, sender=Comment)
def handle_approval_change_pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous_instance = Comment.objects.get(pk=instance.pk)

        if previous_instance.is_approved is False and instance.is_approved is True:
            update_comment_count(instance, increment=True)

        elif previous_instance.is_approved is True and instance.is_approved is False:
            update_comment_count(instance, increment=False)
    elif not instance.pk and instance.is_approved:
        update_comment_count(instance, increment=True)


@receiver(post_delete, sender=Comment)
def update_comment_count_on_delete(sender, instance, **kwargs):
    if instance.is_approved:
        update_comment_count(instance, increment=False)


@receiver(pre_save, sender=Comment)
def set_approved_at(sender, instance, **kwargs):
    if not instance.pk or not hasattr(instance, 'is_approved'):
        return
    
    old = sender.objects.filter(pk=instance.pk).only(
        'is_approved', 'approved_at'
    ).first()
    
    if (
        old
        and not old.is_approved
        and instance.is_approved
        and not old.approved_at
    ):
        instance.approved_at = timezone.now()
