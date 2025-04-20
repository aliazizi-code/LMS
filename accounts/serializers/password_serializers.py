from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from utils.otp import verify_otp_reset_password

from accounts.serializers import PhoneNumberField
from accounts.models import User


class PasswordField(serializers.CharField):
    default_validators = [
        RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#\$%\^&\*\(\)-_\+=\{\}:\;"<>,\.?\/]).{8,}$',
            message="Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character."
        )
    ]

    def __init__(self, *args, **kwargs):
        super(PasswordField, self).__init__(required=True, write_only=True, *args, **kwargs)


class BasePasswordSerializer(serializers.Serializer):
    password = PasswordField()


class ChangePasswordSerializer(BasePasswordSerializer):
    old_password = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        
        if not user.check_password(value):
            raise serializers.ValidationError('رمز عبور فعلی اشتباه است.')
        return value
    
    def validate(self, attrs):
        if attrs['old_password'] == attrs['password']:
            raise serializers.ValidationError({'password': 'رمز عبور جدید نباید مشابه رمز عبور فعلی باشد.'})
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    phone = PhoneNumberField(max_length=13)

    def validate_phone(self, value):
        get_object_or_404(User, phone=value)
        return value


class CheckPhoneSerializer(serializers.Serializer):
    phone = PhoneNumberField(max_length=13)

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError({'phone': 'شماره تلفن وارد شده در سیستم ثبت نشده است.'})
        return value
    

class ResetPasswordSerializer(BasePasswordSerializer):
    phone = PhoneNumberField(max_length=13)
    otp = serializers.IntegerField(required=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
        otp = attrs.get('otp')
        user = get_object_or_404(User, phone)

        if not verify_otp_reset_password(phone, otp):
            raise serializers.ValidationError({'otp': 'Invalid OTP provided. Please try again.'})
        attrs['user'] = user
        return attrs
    


    
    
