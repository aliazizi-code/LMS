from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from accounts.models import JobCategory, EmployeeProfile
from courses.models import Course
# from blog.models import Article # (uncomment if needed)


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


@receiver(post_migrate)
def author_permission(sender, **kwargs):
    if sender.name == 'accounts':
        content_type = ContentType.objects.get_for_model(Course)
        permission, _ = Permission.objects.get_or_create(
            codename='can_author',
            name='Can author',
            content_type=content_type,
        )
        event_creators_group, _ = Group.objects.get_or_create(name='Author')
        event_creators_group.permissions.add(permission)

@receiver(post_migrate)
def create_permissions(sender, **kwargs):
    if sender.name == 'accounts':
        
        # Create Teacher Permission
        content_type_course = ContentType.objects.get_for_model(Course)
        teacher_permission, _ = Permission.objects.get_or_create(
            codename='can_teacher',
            name='Can teacher',
            content_type=content_type_course,
        )
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        teacher_group.permissions.add(teacher_permission)

        # Create Employee Permission
        content_type_employee = ContentType.objects.get_for_model(EmployeeProfile)
        employee_permission, _ = Permission.objects.get_or_create(
            codename='can_employee',
            name='Can employee',
            content_type=content_type_employee,
        )
        employee_group, _ = Group.objects.get_or_create(name='Employee')
        employee_group.permissions.add(employee_permission)
        
        # Create Author Permission (uncomment if needed)
        # content_type_blog = ContentType.objects.get_for_model(Article)
        # author_permission, _ = Permission.objects.get_or_create(
        #     codename='can_author',
        #     name='Can author',
        #     content_type=content_type_blog,
        # )
        # author_group, _ = Group.objects.get_or_create(name='Author')
        # author_group.permissions.add(author_permission)