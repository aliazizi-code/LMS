from PIL import Image
import tempfile

from django.urls import reverse
from django.test import override_settings, TestCase
from http.cookies import SimpleCookie
from django.utils.timezone import timedelta, datetime
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from freezegun import freeze_time

from accounts.models import User, Job, Skill, EmployeeProfile, UserProfile, SocialLink


class APITestCase(TestCase):
    client_class = APIClient
    
    def login(self, user):
        self.refresh = RefreshToken.for_user(user)
        self.client.cookies['access_token'] = str(self.refresh.access_token)
        self.client.cookies['refresh_token'] = str(self.refresh)


# region Auth

class TestRequestOTPView(APITestCase):
    @classmethod
    def setUpTestData(self):
        self.valid_phone = "+989123456789"
        self.valid_new_phone = "+989123456780"
        self.url = reverse('request-otp')
        self.user = User.objects.create(phone=self.valid_phone)
        
    @override_settings(DEBUG=True)
    @patch('accounts.views.generate_otp_auth_num')
    @patch('accounts.views.send_otp_to_phone_tasks.delay')
    def test_request_otp_success_existing_user(self, mock_send_otp, mock_generate_otp):
        mock_generate_otp.return_value = "123456"

        response = self.client.post(self.url, {"phone": self.valid_phone})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["created"])
        self.assertEqual(response.data['otp'], '123456')
        
        mock_generate_otp.assert_called_once_with(self.valid_phone)
        mock_send_otp.assert_called_once_with("123456")
    
    @override_settings(DEBUG=True)
    @patch('accounts.views.generate_otp_auth_num')
    @patch('accounts.views.send_otp_to_phone_tasks.delay')
    def test_request_otp_success_new_user(self, mock_send_otp, mock_generate_otp):
        mock_generate_otp.return_value = "123456"

        response = self.client.post(self.url, {"phone": self.valid_new_phone})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["created"])
        self.assertEqual(response.data['otp'], '123456')
        
        mock_generate_otp.assert_called_once_with(self.valid_new_phone)
        mock_send_otp.assert_called_once_with("123456")

    @override_settings(DEBUG=True)
    @patch('accounts.views.generate_otp_auth_num')
    @patch('accounts.views.send_otp_to_phone_tasks.delay')
    def test_invalid_phone_format(self, mock_send_otp, mock_generate_otp):
        response = self.client.post(self.url, {"phone": "invalid"})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)
    
    def request_at(self, frozen_time):
        with freeze_time(frozen_time):
            return self.client.post(self.url, {'phone': self.valid_phone})
        
    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        OTP={
            "EXPIRATION_TIME_SECONDS": 120,
            "LONG_TIME_SECONDS": 2 * 60 * 60,
            "LONG_MAX_REQUESTS": 20,
            "VALID_WINDOW": 1,
        },
        DEBUG=False,
    )
    @patch('accounts.views.send_otp_to_phone_tasks.delay')
    @patch('accounts.views.generate_otp_auth_num')
    def test_throttling_protection(self, mock_generate_otp, mock_send_otp):
        mock_generate_otp.return_value = '111111'
        start_time = datetime(2025, 1, 1, 12, 0, 0)
        
        for i in range(20):
            response = self.request_at(start_time + timedelta(minutes=i))   
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        response = self.request_at(start_time + timedelta(hours=2, seconds=1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.request_at(start_time + timedelta(hours=2, seconds=2))
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        for i in range(2):
            response = self.client.post(self.url, {'phone': self.valid_phone})   
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class TestVerifyOTPView(APITestCase):
    @classmethod
    def setUpTestData(self):
        self.valid_phone = "+989123456789"
        self.valid_new_phone = "+989123456780"
        self.url = reverse('verify-otp')
        self.user = User.objects.create(phone=self.valid_phone)
    
    @override_settings(DEBUG=True)
    @patch('accounts.serializers.verify_otp_auth_num', return_value=True)
    def test_success_existing_user(self, mock_verify_otp):
        response = self.client.post(self.url, {"phone": self.valid_phone, "otp": 123456})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], self.valid_phone)
        self.assertFalse(response.data['created'])
        self.assertIn('access_token', response.cookies.keys())
        self.assertIn('refresh_token', response.cookies.keys())
        mock_verify_otp.assert_called_once_with(self.valid_phone, 123456)
    
    @override_settings(DEBUG=True)
    @patch('accounts.serializers.verify_otp_auth_num', return_value=True)
    def test_success_new_user(self, mock_verify_otp):
        response = self.client.post(self.url, {"phone": self.valid_new_phone, "otp": 123456})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["phone"], self.valid_new_phone)
        self.assertTrue(response.data['created'])
        self.assertIn('access_token', response.cookies.keys())
        self.assertIn('refresh_token', response.cookies.keys())
        mock_verify_otp.assert_called_once_with(self.valid_new_phone, 123456)
        
    @override_settings(DEBUG=True)
    @patch('accounts.serializers.verify_otp_auth_num', return_value=False)
    def test_otp_invalid(self, mock_verify_otp):
        response = self.client.post(self.url, {"phone": self.valid_phone, "otp": 123456})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
        mock_verify_otp.assert_called_once_with(self.valid_phone, 123456)

    def test_missing_otp(self):
        response = self.client.post(self.url, {"phone": self.valid_phone})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
    
    def test_invalid_phone(self):
        response = self.client.post(self.url, {"phone": "invalid", "otp": 123456})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
    
    def test_missing_phone(self):
        response = self.client.post(self.url, {"otp": 123456})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
    

class TestPhoneLoginView(APITestCase):
    @classmethod
    def setUpTestData(self):
        self.valid_phone = "+989123456789"
        self.url = reverse('phone-login')
        self.user = User.objects.create(phone=self.valid_phone)
        self.user.set_password("Pass123?")
        self.user.save()
    
    def test_login_success(self):
        response = self.client.post(self.url, {"phone": self.valid_phone, "password": "Pass123?"})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies.keys())
        self.assertIn('refresh_token', response.cookies.keys())
    
    def test_invalid_password(self):
        response = self.client.post(self.url, {"phone": self.valid_phone, "password": "invalid"})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
    
    def test_missing_password(self):
        response = self.client.post(self.url, {"phone": self.valid_phone})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
        
    def test_invalid_phone(self):
        response = self.client.post(self.url, {"phone": "invalid", "password": "Pass123?"})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())
    
    def test_missing_phone(self):
        response = self.client.post(self.url, {"password": "Pass123?"})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())


class TestLogoutView(APITestCase):
    def setUp(self):
        self.url_logout = reverse('logout')
        self.user = User.objects.create(phone="+989123456789")
        
    def test_logout_success(self):
        self.login(self.user)
        
        self.assertIn('access_token', self.client.cookies.keys())
        response = self.client.post(self.url_logout)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['access_token'].value, "")
        self.assertEqual(response.cookies['refresh_token'].value, "")
    
    def test_logout_without_login(self):
        response = self.client.post(self.url_logout)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())


class TestRefreshTokenView(APITestCase):
    @classmethod
    def setUpTestData(self):
        self.url = reverse('token-refresh')
        self.user = User.objects.create(phone="+989123456789")
        self.user.set_password("Pass123?")
        self.user.save()
        
    def test_refresh_token_success(self):
        response_login = self.client.post(reverse('phone-login'), {"phone": "+989123456789", "password": "Pass123?"})
        self.assertIn('access_token', self.client.cookies.keys())
        self.assertIn('access_token', self.client.cookies.keys())
        
        response_refresh = self.client.post(self.url)
        self.assertEqual(response_refresh.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', self.client.cookies.keys())
        self.assertIn('refresh_token', self.client.cookies.keys())
        
        self.assertNotEqual(self.client.cookies['access_token'].value, response_login.cookies['access_token'].value)
        self.assertEqual(self.client.cookies['refresh_token'].value, response_login.cookies['refresh_token'].value)
    
    def test_refresh_token_without_login(self):
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('access_token', response.cookies.keys())
        self.assertNotIn('refresh_token', response.cookies.keys())

# endregion

# region Employee and Team

class EmployeeTestMixin:
    """Mixin containing shared test methods for employee views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('employee-list')
        cls.url1 = reverse('employee-detail', kwargs={'username': 'username1'})
        cls.url2 = reverse('employee-detail', kwargs={'username': 'username2'})
        cls.url3 = reverse('employee-detail', kwargs={'username': 'username3'})
        cls.url4 = reverse('employee-detail', kwargs={'username': 'username4'})
        cls.url_hidden = reverse('employee-detail', kwargs={'username': 'hidden-user'})
        
        cls.job1 = Job.objects.create(name="Job 1")
        
        cls.skill1 = Skill.objects.create(name="Skill 1")
        cls.skill2 = Skill.objects.create(name="Skill 2")
        
        for i in range(1, 5):
            cls.test_image = cls.create_test_image(f"username{i}")
            cls.create_employee(i, cls.job1, [cls.skill1, cls.skill2], ["role1", "role2"])
        
        cls.create_hidden_employee("hidden-user", cls.job1, [cls.skill1, cls.skill2])
    
    @classmethod
    def create_test_image(cls, username):
        """Helper method to create a test image with consistent filename"""
        image = Image.new('RGB', (100, 100), color='red')
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file, format='JPEG')
        tmp_file.seek(0)
        return SimpleUploadedFile(
            name=f'avatar_{username}.jpg',
            content=tmp_file.read(),
            content_type='image/jpeg'
        )
    
    @classmethod
    def create_employee(cls, i, job, skills, roles, display=True):
        """Helper method to create employee with complete profile"""
        user = User.objects.create(
            phone=f"+98912345678{i}",
            first_name=f"First{i}",
            last_name=f"Last{i}"
        )
        
        user_profile = UserProfile.objects.create(
            user=user,
            job=job,
            age=20+i,
            gender=UserProfile.Gender.male if i % 2 else UserProfile.Gender.female,
            bio=f"Bio for user {i}",
            avatar=cls.test_image
        )
        user_profile.skills.add(*skills)
        
        employee_profile = EmployeeProfile.objects.create(
            user_profile=user_profile,
            username=f"username{i}",
        )
        employee_profile.roles.set(roles)
        
        SocialLink.objects.create(
            social_media_type=SocialLink.SocialMediaType.github,
            link=f"https://github.com/username{i}",
            employee_profile=employee_profile, 
        )
        
        if display:
            group = Group.objects.create(name=f"Group {i}")
            group.custom_group.is_display = True
            group.custom_group.save()
            user.groups.add(group)
        
        return employee_profile

    @classmethod
    def create_hidden_employee(cls, username, job, skills):
        """Helper to create hidden employee profile"""
        hidden_user = User.objects.create(
            phone=f"+98911111111",
            first_name="Hidden",
            last_name="User"
        )
        
        hidden_profile = UserProfile.objects.create(
            user=hidden_user,
            job=job,
            age=30,
            gender=UserProfile.Gender.female,
            bio="Hidden bio",
            avatar=cls.create_test_image(username)
        )
        hidden_profile.skills.add(*skills)
        
        employee_profile = EmployeeProfile.objects.create(
            user_profile=hidden_profile,
            username=username
        )
        employee_profile.roles.set(["role1", "role2"])
        
        hidden_group = Group.objects.create(name="Hidden Group")
        hidden_group.custom_group.is_display = False
        hidden_group.custom_group.save()
        hidden_user.groups.add(hidden_group)
        
        SocialLink.objects.create(
            social_media_type=SocialLink.SocialMediaType.github,
            link=f"https://github.com/{username}",
            employee_profile=employee_profile
        )
        
        return employee_profile


class TestEmployeeListView(EmployeeTestMixin, APITestCase):
    def test_get_employee_list_success(self):
        """Test successful API response"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        for i in range(0, 5):
            self.assertIn('username', response.data[i])
            self.assertIn('full_name', response.data[i])
            self.assertIn('avatar_thumbnail', response.data[i])
            
            self.assertTrue(response.data[i]['username'])
            self.assertTrue(response.data[i]['full_name'])
            self.assertTrue(response.data[i]['avatar_thumbnail'])


class TestEmployeeDetailView(EmployeeTestMixin, APITestCase):
    def test_get_employee_detail_success(self):
        """Test successful API response"""
        for url, i in zip([self.url1, self.url2, self.url3, self.url4], range(1, 5)):
            response = self.client.get(url)
            response.data.pop('avatar')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            self.assertEqual(
                response.data,
                {
                    'full_name': f'First{i} Last{i}',
                    'bio': f'Bio for user {i}',
                    'groups': [f'Group {i}'],
                    'skills': ['Skill 2', 'Skill 1'],
                    'roles': ['role1', 'role2'],
                    'social_links': [{
                        'link': f'https://github.com/username{i}',
                        'type_social': 'github'
                    }],
                }
            )

        response = self.client.get(self.url_hidden)
        response.data.pop('avatar')
        self.assertEqual(
                response.data,
                {
                    'full_name': 'Hidden User',
                    'bio': "Hidden bio",
                    'groups': [],
                    'skills': ['Skill 2', 'Skill 1'],
                    'roles': ['role1', 'role2'],
                    'social_links': [{
                        'link': f'https://github.com/hidden-user',
                        'type_social': 'github'
                    }],
                }
            )

# endregion

# region Password

class TestSetPasswordView(APITestCase):
    def setUp(self):
        self.user = User.objects.create(phone='+989123456789')
        
        self.url = reverse('set-password')
        self.valid_data = {'password': "Pass123?"}
        self.invalid_data = {'password': "invalid"}
        
        self.login(self.user)
    
    def test_set_password_success(self):
        self.assertFalse(bool(self.user.password))
        
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Pass123?"))
    
    def test_set_password_has_password(self):
        self.user.set_password('Pass123?')
        self.user.save()
        self.assertTrue(self.user.check_password("Pass123?"))
        
        self.assertTrue(bool(self.user.password))
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.check_password("Pass123?"))
    
    def test_set_password_invalid_token(self):
        self.client.cookies['access_token'] = 'invalid.token.here'
        
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_set_invalid_password(self):
        self.assertFalse(bool(self.user.password))
        
        response = self.client.post(self.url, self.invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password("invalid"))
        self.assertFalse(bool(self.user.password))


class TestChangePasswordView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("change-password")
        cls.user = User.objects.create(phone="+989123456789")
        cls.new_pass = "NewPass1?"
        cls.valid_old_pass = "Pass123?"
        cls.invalid_old_pass = "invalid"
    
    def test_valid_old_pass(self):
        self.user.set_password(self.valid_old_pass)
        self.user.save()
        
        self.login(self.user)
        self.assertTrue(bool(self.user.password))
        
        response = self.client.post(
            self.url,
            {'old_password': self.valid_old_pass, 'password': self.new_pass}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(self.new_pass))
    
    def test_invalid_old_pass(self):
        self.user.set_password(self.valid_old_pass)
        self.user.save()
        
        self.login(self.user)
        self.assertTrue(bool(self.user.password))
        
        response = self.client.post(
            self.url,
            {'old_password': self.invalid_old_pass, 'password': self.new_pass}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.new_pass))
        
    def test_missing_old_password(self):
        self.user.set_password(self.valid_old_pass)
        self.user.save()
        
        self.login(self.user)
        self.assertTrue(bool(self.user.password))
        
        response = self.client.post(
            self.url,
            {'password': self.new_pass}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.new_pass))
        
    def test_missing_password(self):
        self.user.set_password(self.valid_old_pass)
        self.user.save()
        
        self.login(self.user)
        self.assertTrue(bool(self.user.password))
        
        response = self.client.post(
            self.url,
            {'old_password': self.invalid_old_pass}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.new_pass))

    def test_not_existing_password(self):
        self.login(self.user)
        self.assertFalse(bool(self.user.password))
        
        response = self.client.post(
            self.url,
            {'old_password': self.valid_old_pass, 'password': self.new_pass}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(bool(self.user.password))
        
    def test_without_login(self):
        self.user.set_password(self.valid_old_pass)
        self.user.save()
        
        self.assertTrue(bool(self.user.password))
        response = self.client.post(
            self.url,
            {'old_password': self.valid_old_pass, 'password': self.new_pass}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(self.user.check_password(self.new_pass))



  