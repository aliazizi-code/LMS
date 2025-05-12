from django.test import TestCase
from django.contrib.auth.models import Group
from accounts.models import CustomGroup
from django.core.management import call_command


class TestCustomGroupSignals(TestCase):
        
    def test_create_custom_group_on_group_creation(self):
        group = Group.objects.create(name='Test Group')
        custom_group = CustomGroup.objects.filter(group=group).first()
        
        self.assertIsNotNone(custom_group,  "CustomGroup was not created for the new Group.")
        self.assertEqual(custom_group.group, group, "CustomGroup is not linked to the correct Group.")


class TestPermissionsSignals(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Call the command to create permissions
        call_command('migrate', 'accounts')
        
    def test_teacher_permission(self):
        group = Group.objects.filter(name='مدرسین')
        permission_exists = group.first().permissions.filter(codename='can_teacher').exists()
        
        self.assertTrue(group.exists(), "The 'مدرسین' group does not exist.")
        self.assertTrue(permission_exists, "Permission 'can_teacher' was not added to the 'مدرسین' group.")
        
    def test_employee_permission(self):
        group = Group.objects.filter(name='کارمندان')
        permission_exists = group.first().permissions.filter(codename='can_employee').exists()
        
        self.assertTrue(group.exists(), "The 'کارمندان' group does not exist.")
        self.assertTrue(permission_exists, "Permission 'can_employee' was not added to the 'کارمندان' group.")
