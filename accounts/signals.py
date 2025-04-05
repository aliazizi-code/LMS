from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from accounts.models import JobCategory
from courses.models import Course


@receiver(post_save, sender=JobCategory)
def update_active_status_of_descendants(sender, instance, **kwargs):
    descendants = instance.get_descendants(include_self=True)
    descendants.update(is_active=instance.is_active)


@receiver(post_migrate)
def teacher_permission(sender, **kwargs):
    if sender.name == 'accounts':
        content_type = ContentType.objects.get_for_model(Course)
        permission, _ = Permission.objects.get_or_create(
            codename='can_teacher',
            name='Can teacher',
            content_type=content_type,
        )
        event_creators_group, _ = Group.objects.get_or_create(name='Teacher')
        event_creators_group.permissions.add(permission)
