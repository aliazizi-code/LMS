from django.test import TestCase
from accounts.forms import UserCreationForm, UserRegistrationForm
from accounts.models import User


class TestUserCreationForm(TestCase):
    def test_valid_data(self):
        form_data = {
            'phone': '+989123456789',
            'password1': 'password123',
            'password2': 'password123'
        }
        
        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), "Form should be valid with correct data")
        
    def test_empty_data(self):
        form = UserCreationForm(data={})
        self.assertFalse(form.is_valid(), "Form should be invalid with empty data")
        self.assertEqual(len(form.errors), 3, "Should show errors for all required fields (phone, password1, password2)")
        
    def test_exists_password2(self):
        form_data = {
            'phone': '+989123456789',
            'password1': 'password123',
            'password2': 'differentpassword'
        }
        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid(), "Form should be invalid when passwords don't match")
        self.assertIn('password2', form.errors, "Should show error on password2 field for mismatched passwords")
        self.assertEqual(len(form.errors), 1, "Should only show password mismatch error")
        self.assertTrue(form.has_error('password2'), "Password2 field should have error")


class TestUserRegistrationForm(TestCase):
    def test_valid_data(self):
        form_data = {
            'phone': '+989123456789'
        }
        
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), "Form should be valid with correct data")
    
    def test_exists_phone(self):
        # Assuming a user with this phone number already exists
        form_data = {
            'phone': '+989123456789'
        }
        
        # Create a user with the same phone number
        User.objects.create(phone=form_data['phone'])
        
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid(), "Form should be invalid when phone number already exists")
        self.assertIn('phone', form.errors, "Should show error for existing phone number")
        self.assertEqual(len(form.errors), 1, "Should only show error for phone field")
        
    def test_empty_data(self):
        form = UserRegistrationForm(data={})
        self.assertFalse(form.is_valid(), "Form should be invalid with empty data")
        self.assertIn('phone', form.errors, "Should show error for phone field")
        self.assertEqual(len(form.errors), 1, "Should only show error for phone field")
