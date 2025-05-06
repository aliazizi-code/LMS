from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from accounts.models import EmployeeProfile, CustomGroup
from courses.models import Course
# from blog.models import Article # (uncomment if needed)
from utils import update_descendants_active_status


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
        teacher_group, _ = Group.objects.get_or_create(name='مدرسین')
        teacher_group.permissions.add(teacher_permission)

        # Create Employee Permission
        content_type_employee = ContentType.objects.get_for_model(EmployeeProfile)
        employee_permission, _ = Permission.objects.get_or_create(
            codename='can_employee',
            name='Can employee',
            content_type=content_type_employee,
        )
        employee_group, _ = Group.objects.get_or_create(name='کارمندان')
        employee_group.permissions.add(employee_permission)
        
        # Create Author Permission (uncomment if needed)
        # content_type_blog = ContentType.objects.get_for_model(Article)
        # author_permission, _ = Permission.objects.get_or_create(
        #     codename='can_author',
        #     name='Can author',
        #     content_type=content_type_blog,
        # )
        # author_group, _ = Group.objects.get_or_create(name='نویسندگان')
        # author_group.permissions.add(author_permission)


@receiver(post_save, sender=Group)
def create_custom_group(sender, instance, created, **kwargs):
    if created:
        CustomGroup.objects.create(group=instance)
