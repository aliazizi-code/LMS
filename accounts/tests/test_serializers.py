from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock

from utils import BaseNameRelatedField
from accounts.models import Job, Skill, SocialLink
from accounts.models import User, UserProfile, EmployeeProfile
from accounts.serializers import (
    # Fields
    PhoneNumberField,
    PasswordField,
    SkillRelatedField,
    JobRelatedField,
    
    # Serializers
    RequestOTPSerializer,
    VerifyOTPSerializer,
    BaseLoginSerializer,
    PhoneLoginSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    ChangePasswordSerializer,
    CheckPhoneSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    ChangePhoneRequestSerializer,
    ChangePhoneVerifySerializer,
)


# region custom field

class TestPhoneNumberField(TestCase):
    def setUp(self):
        self.field = PhoneNumberField()
        
    def test_valid_phone_number(self):
        """Test valid phone number formats"""
        valid_numbers = [
            '+981234567890',
            '+989876543210',
        ]
        
        for number in valid_numbers:
            self.assertEqual(
                self.field.run_validation(number), number,
                f"Phone number {number} should be considered valid"
            )
    
    def test_invalid_phone_number(self):
        """Test invalid phone number formats"""
        
        invalid_numbers = [
            '989123456789',    # Missing +
            '+98123456789',    # Wrong prefix
            '+98912345678',    # Less than 12 digits
            '+9891234567890',  # More than 12 digits
            '+98912abc6789',   # Contains letters
            '09123456789',     # Old format
            '+98912 345 6789'  # Contains spaces
        ]
        
        for number in invalid_numbers:
            with self.assertRaises(ValidationError, msg=f"Phone number {number} should be considered invalid"):
                self.field.run_validation(number)


class TestPasswordField(TestCase):
    def setUp(self):
        self.field = PasswordField()
    
    def test_valid_password(self):
        valid_passwords = [
            'SecurePass123!',
            'Another1@Pass',
            'Test@1234',
            'L0ngP@sswordWithSpecialChars!'
        ]
        
        for password in valid_passwords:
            self.assertEqual(
                self.field.run_validation(password), password,
                f"Password '{password}' should be considered valid"
            )
    
    def test_invalid_password(self):
        invalid_passwords = [
            'short1!',           # Less than 8 chars
            'nocapitals1!',       # No uppercase
            'NOLOWERCASE1!',      # No lowercase
            'NoNumbers!',         # No digits
            'MissingSpecial123',  # No special chars
            'alllowercase',       # Only lowercase
            '12345678',           # Only digits
            '!@#$%^&*',          # Only special chars
            'PasswordWithoutSpecial'  # No special chars
        ]
        
        for password in invalid_passwords:
            with self.assertRaises(ValidationError, msg=f"Password '{password}' should be considered invalid"):
                self.field.run_validation(password)
        
    def test_field_properties(self):
        self.assertTrue(self.field.write_only, "Field should be write_only")
        self.assertEqual(
            self.field.style.get('input_type'),
            'password',
            "Input type should be 'password'"
        )


class TestBaseNameRelatedField(TestCase):
    @classmethod
    def setUpTestData(self):
        self.skill_queryset = Skill.objects.all()
    
    def setUp(self):
        self.skill = Skill.objects.create(name='Python')

    def test_base_field_representation(self):
        """Test basic representation with existing object"""
        field = BaseNameRelatedField(queryset=self.skill_queryset)
        field.model = Skill
        result = field.to_representation(self.skill)
        self.assertEqual(result, 'Python')

    def test_missing_object(self):
        """Test handling of non-existent objects"""
        field = BaseNameRelatedField(queryset=self.skill_queryset)
        field.model = Skill
        
        skill_id = self.skill.id
        self.skill.delete()
        
        fake_skill = type('FakeSkill', (), {'pk': skill_id})()
        result = field.to_representation(fake_skill)
        # result = field.to_representation(Skill.objects.filter(pk=skill_id).first())
        
        self.assertIsNone(result, "Should return None for deleted objects")
        
    def test_none_value(self):
        """Test handling of None input"""
        field = BaseNameRelatedField(queryset=self.skill_queryset)
        result = field.to_representation(None)
        self.assertIsNone(result)


class TestSkillRelatedField(TestCase):
    def test_skill_representation(self):
        """Skill field should return skill name"""
        skill = Skill.objects.create(name='Django')
        field = SkillRelatedField(queryset=Skill.objects.all())
        result = field.to_representation(skill)
        self.assertEqual(result, 'Django')


class TestJobRelatedField(TestCase):
    def test_job_representation(self):
        """Job field should return job title"""
        job = Job.objects.create(name='Backend Developer')
        field = JobRelatedField(queryset=Job.objects.all())
        result = field.to_representation(job)
        self.assertEqual(result, 'Backend Developer')

# endregion        

# region Auth

class TestRequestOTPSerializer(TestCase):
    def test_valid(self):
        valid_data = {'phone': '+989876543210'}
        serializer = RequestOTPSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
    def test_invalid(self):
        invalid_data = [
            {'phone': ''},
            {'phone': '09876543210'},
            {'phone': 'invalid'},
            {'phone': '+12345678901234'},
        ]
        
        for data in invalid_data:
            serializer = RequestOTPSerializer(data=data)
            with self.assertRaises(ValidationError):
                serializer.is_valid(raise_exception=True)


class TestVerifyOTPSerializer(TestCase):
    def setUp(self):
        self.valid_data = {
            'phone': '+989123456789',
            'otp': 123456
        }
    
    @patch('accounts.serializers.verify_otp_auth_num')
    def test_valid_otp(self, mock_verify):
        """Test with valid OTP"""
        mock_verify.return_value = True
        
        serializer = VerifyOTPSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['otp'], 123456)
        self.assertEqual(serializer.validated_data['phone'], self.valid_data['phone'])
    
    @patch('accounts.serializers.verify_otp_auth_num')
    def test_invalid(self, mock_verify):
        """Test with invalid OTP"""
        mock_verify.return_value = False
        
        serializer = VerifyOTPSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp', serializer.errors)
        
    def test_missing_otp(self):
        """Test when OTP is missing"""
        invalid_data = {'phone': '+989123456789'}
        serializer = VerifyOTPSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp', serializer.errors)
        
    @patch('accounts.serializers.verify_otp_auth_num')
    def test_invalid_phone_formats(self, mock_verify):
        """Test various invalid phone number formats"""
        mock_verify.return_value = True
        invalid_cases = [
            {
                'description': 'Number with 0 prefix',
                'data': {'phone': '09123456789', 'otp': 123456},
            },
            {
                'description': 'Short length',
                'data': {'phone': '+989123456', 'otp': 123456},
            },
            {
                'description': 'Long length',
                'data': {'phone': '+9891234567890', 'otp': 123456},
            },
            {
                'description': 'No country code',
                'data': {'phone': '9123456789', 'otp': 123456},
            },
            {
                'description': 'Wrong country code',
                'data': {'phone': '+90123456789', 'otp': 123456},
            },
            {
                'description': 'Contains letters',
                'data': {'phone': '+98abc456789', 'otp': 123456},
            },
            {
                'description': 'Contains spaces',
                'data': {'phone': '+98 912 345 6789', 'otp': 123456},
            },
            {
                'description': 'Empty phone',
                'data': {'phone': '', 'otp': 123456},
            },
            {
                'description': 'Missing phone',
                'data': {'phone': None, 'otp': 123456},
            },
        ]

        for case in invalid_cases:
            description = case['description']
            with self.subTest(description):
                serializer = VerifyOTPSerializer(data=case['data'])
                self.assertFalse(serializer.is_valid(), f"Test failed for case: {description}")
                self.assertIn('phone', serializer.errors, f"Phone error missing for case: {description}")


class TestPhoneLoginSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            'phone': '+989123456789',
            'password': 'testPass123?'
        }

        cls.user = User.objects.create_user(**cls.user_data)
        
    def test_inheritance_structure(self):
        """Test if PhoneLoginSerializer properly inherits from BaseLoginSerializer"""
        fields = PhoneLoginSerializer().get_fields()
        
        self.assertTrue(issubclass(PhoneLoginSerializer, BaseLoginSerializer))
        self.assertIn('phone', fields)
        self.assertIn('password', fields)
    
    def test_get_user_implementation(self):
        """Test if get_user is properly implemented"""
        serializer = PhoneLoginSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.get_user(serializer.validated_data)
        self.assertEqual(user, self.user)
        self.assertIsNotNone(authenticate(phone=self.user_data['phone'] , password=self.user_data['password']))
    
    def test_invalid_credentials(self):
        """Test both invalid phone and password return password error"""
        test_cases = [
            {
                'description': 'invalid_phone',
                'data': {'phone': '+989876543210', 'password': 'testPass123?'}
            },
            {
                'description': 'invalid_password', 
                'data': {'phone': '+989123456789', 'password': 'invalid'}
            },
        ]
        
        for case in test_cases:
            with self.subTest(case['description']):
                serializer = PhoneLoginSerializer(data=case['data'])
                self.assertFalse(serializer.is_valid())
                self.assertIn('password', serializer.errors)

# endregion

# region Employee and Team

class TestEmployeeListSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+989123456789',
        )
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        self.user_profile = UserProfile.objects.create(user=self.user)
        
        self.employee = EmployeeProfile.objects.create(
            username='employee1',
            user_profile=self.user_profile
        )
    
    @patch('accounts.models.UserProfile.avatar_thumbnail')
    def test_serializer_fields(self, mock_avatar):
        """Test serializer returns expected fields"""
        
        mock_avatar.url = 'http://example.com/media/avatar_thumb.jpg'
        
        serializer = EmployeeListSerializer(instance=self.employee)
        self.assertEqual(
            set(serializer.data.keys()),
            {'username', 'full_name', 'avatar_thumbnail'}
        )
        self.assertEqual(serializer.data['avatar_thumbnail'], mock_avatar.url)
        
    def test_full_name_method(self):
        """Test get_full_name method"""
        serializer = EmployeeListSerializer(instance=self.employee)
        self.assertEqual(serializer.get_full_name(self.employee), 'John Doe')
        
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        self.assertEqual(serializer.get_full_name(self.employee), None)
        
    @patch('accounts.models.UserProfile.avatar_thumbnail')
    def test_avatar_thumbnail_method(self, mock_thumbnail):
        """Test get_avatar_thumbnail method"""
        mock_thumbnail.url = '/media/avatars/test_thumb.jpg'
        
        serializer = EmployeeListSerializer(instance=self.employee)
        self.assertEqual(
            serializer.get_avatar_thumbnail(self.employee),
            mock_thumbnail.url
        )
        
        self.user_profile.avatar_thumbnail = None
        self.user_profile.save()
        self.assertIsNone(
            serializer.get_avatar_thumbnail(self.employee)
        )


class TestEmployeeDetailSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+989123456789',
        )
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            bio='Experienced developer',
        )
        self.user_profile.avatar = MagicMock()
        self.user_profile.avatar.url = '/media/avatars/john.jpg'
        
        self.employee = EmployeeProfile.objects.create(
            username='john_doe',
            user_profile=self.user_profile
        )
        
        self.skill1 = Skill.objects.create(name='Python', is_active=True)
        self.skill2 = Skill.objects.create(name='Django', is_active=True)
        self.user_profile.skills.add(self.skill1, self.skill2)
        
        self.group = Group.objects.create(name='Developers')
        self.group.custom_group.is_display = True
        self.group.custom_group.save()
        self.user.groups.add(self.group)
        
        self.social_link = SocialLink.objects.create(
            employee_profile=self.employee,
            link='https://www.linkedin.com/johndoe',
            social_media_type='linkedin'
        )
    
    def test_serializer_output(self):
        request = MagicMock()
        serializer = EmployeeDetailSerializer(
            instance=self.employee,
            context={'request': request}
        )
        
        expected_data = {
            'full_name': 'John Doe',
            'bio': 'Experienced developer',
            'avatar': '/media/avatars/john.jpg',
            'groups': ['Developers'],
            'skills': ['Django', 'Python'],
            'roles': [],
            'social_links': [
                {
                    'link': 'https://www.linkedin.com/johndoe',
                    'type_social': 'linkedin'
                }
            ]
        }
        
        self.assertDictEqual(serializer.data, expected_data)
    
    def test_avatar_none(self):
        self.user_profile.avatar = None
        serializer = EmployeeDetailSerializer(instance=self.employee)
        self.assertIsNone(serializer.data['avatar'])
    
    def test_empty_skills(self):
        self.user_profile.skills.clear()
        serializer = EmployeeDetailSerializer(instance=self.employee)
        self.assertEqual(serializer.data['skills'], [])
    
    def test_inactive_skills(self):
        skill = Skill.objects.create(name='PHP', is_active=False)
        self.user_profile.skills.add(skill)
        serializer = EmployeeDetailSerializer(instance=self.employee)
        self.assertNotIn('PHP', serializer.data['skills'])
    
    def test_hidden_groups(self):
        hidden_group = Group.objects.create(name='Hidden')
        hidden_group.custom_group.is_display = False
        hidden_group.custom_group.save()
        self.user.groups.add(hidden_group)
        
        serializer = EmployeeDetailSerializer(instance=self.employee)
        self.assertNotIn('Hidden', serializer.data['groups'])

# endregion

# region Password

class TestChangePasswordSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            'phone': '+989123456789',
            'password': 'testPass123?'
        }
        cls.factory = APIRequestFactory()
        cls.user = User.objects.create_user(**cls.user_data)
        cls.request = cls.factory.post('/')
        cls.request.user = cls.user
    
    def test_missing_old_password(self):
        """Test various invalid cases for old password validation"""
        invalid_cases = [
            {
                'description': 'Incorrect old password - should fail validation',
                'data' : {'old_password': 'invalid', 'password': 'newPass123?'}
            },
            {
                'description': 'Empty old password - should fail validation',
                'data' : {'old_password': '', 'password': 'newPass123?'}
            },
            {
                'description': 'Missing old password - should fail validation',
                'data': {'password': 'newPass123?'},
            },
        ]
        
        for case in invalid_cases:
            description = case['description']
            with self.subTest(description):
                serializer = ChangePasswordSerializer(data=case['data'], context={'request': self.request})
                
                self.assertFalse(serializer.is_valid())
                self.assertIn('old_password', serializer.errors)
    
    def test_old_pass_match_pass(self):
        data = {
            'old_password': 'testPass123?',
            'password': 'testPass123?'
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': self.request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
    def test_valid_password_change(self):
        data = {
            'old_password': 'testPass123?',
            'password': 'NewPass123!'
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': self.request})
        
        self.assertTrue(serializer.is_valid())


class TestCheckPhoneSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.valid_phone = '+989123456789'
        User.objects.create_user(phone=cls.valid_phone)

    def test_valid_phone(self):
        data = {'phone': self.valid_phone}
        serializer = CheckPhoneSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['phone'], self.valid_phone)

    def test_invalid_phone_not_in_system(self):
        invalid_phone = '+989876543210'
        data = {'phone': invalid_phone}
        serializer = CheckPhoneSerializer(data=data)
        
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)

    def test_empty_phone(self):
        data = {'phone': ''}
        serializer = CheckPhoneSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)


class TestResetPasswordSerializer(TestCase):
    def setUp(self):
        self.valid_phone = '+989123456789'
        self.user = User.objects.create(phone=self.valid_phone)
        self.valid_otp = 123456
        self.base_data = {
            'phone': self.valid_phone,
            'otp': self.valid_otp,
            'password': 'NewPass123!',
        }
        
    @patch('accounts.serializers.verify_otp_reset_password', return_value=True)
    def test_valid_data(self, mock_verify_otp):
        serializer = ResetPasswordSerializer(data=self.base_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
        mock_verify_otp.assert_called_once_with(self.valid_phone, self.valid_otp)
    
    @patch('accounts.serializers.verify_otp_reset_password', return_value=False)
    def test_invalid_otp(self, mock_verify_otp):
        serializer = ResetPasswordSerializer(data=self.base_data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp', serializer.errors)
        mock_verify_otp.assert_called_once_with(self.valid_phone, self.valid_otp)
        
    @patch('accounts.serializers.verify_otp_reset_password', return_value=True)
    def test_missing_otp(self, mock_verify_otp):
        invalid_data = {
            'phone': self.valid_phone,
            'password': 'NewPass123!',
        }
        serializer = ResetPasswordSerializer(data=invalid_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp', serializer.errors)
        mock_verify_otp.assert_not_called()
    
    def test_nonexistent_phone(self):
        invalid_data = {
            'phone': '+989876543210',
            'otp': self.valid_otp,
            'password': 'NewPass123!',
        }
        serializer = ResetPasswordSerializer(data=invalid_data)
        
        with self.assertRaises(Http404):
            serializer.is_valid(raise_exception=True)
    
    @patch('accounts.serializers.verify_otp_reset_password', return_value=True)
    def test_missing_phone(self, mock_verify_otp):
        invalid_data = {
            'otp': self.valid_otp,
            'password': 'NewPass123!',
        }
        serializer = ResetPasswordSerializer(data=invalid_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)
        mock_verify_otp.assert_not_called()

# endregion

# region Update

class TestUserProfileSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            phone='+989123456789',
            first_name='پویا',
            last_name='محمدی'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            bio='برنامه‌نویس پایتون',
            gender='M',
            age=30
        )
    
    def test_basic_serialization(self):
        serializer = UserProfileSerializer(instance=self.profile)
        
        self.assertEqual(serializer.data['first_name'], 'پویا')
        self.assertEqual(serializer.data['last_name'], 'محمدی')
        self.assertEqual(serializer.data['bio'], 'برنامه‌نویس پایتون')
        self.assertEqual(serializer.data['gender'], 'مرد')
        self.assertEqual(serializer.data['phone'], '+989123456789')
    
    def test_simple_update(self):
        update_data = {
            'first_name': 'علی',
            'last_name': 'رضایی',
            'bio': 'توسعه‌دهنده وب'
        }
        
        serializer = UserProfileSerializer(
            instance=self.profile,
            data=update_data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        self.assertEqual(updated_profile.user.first_name, 'علی')
        self.assertEqual(updated_profile.user.last_name, 'رضایی')
        self.assertEqual(updated_profile.bio, 'توسعه‌دهنده وب')
    
    def test_required_fields(self):
        serializer = UserProfileSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)
        
    def test_read_only_fields(self):
        update_data = {'phone': '+989876543210'}
        serializer = UserProfileSerializer(
            instance=self.profile,
            data=update_data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(self.profile.user.phone, '+989123456789')


class TestChangePhoneRequestSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create(phone='+989123456789')
    
    def test_validate_phone(self):
        serializer = ChangePhoneRequestSerializer(data={'phone': '+989123456789'})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)


class TestChangePhoneVerifySerializer(TestCase):
    
    @patch('accounts.serializers.verify_otp_change_phone')
    def test_validate_otp(self, mock_verify_otp):
        self.user = User.objects.create(phone='+989123456789')
        mock_verify_otp.return_value = False
        data = {
            'phone': '+989123456789',
            'otp': 'wrong_code'
        }
        
        serializer = ChangePhoneVerifySerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp', serializer.errors)

# endregion
