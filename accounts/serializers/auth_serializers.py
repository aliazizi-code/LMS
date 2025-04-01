from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from accounts.models import User
from utils import verify_otp_auth_num


class PhoneNumberField(serializers.CharField):
    default_validators = [
        RegexValidator(
            regex=r'^\+98[0-9]{10}$',
            message="Phone number must be entered in the format: '+9891234567890'. Exactly 12 digits allowed."
        )
    ]


class RequestOTPSerializer(serializers.Serializer):
    phone = PhoneNumberField(max_length=13)


class VerifyOTPSerializer(serializers.Serializer):
    phone = PhoneNumberField(max_length=13)
    otp = serializers.IntegerField(required=True)

    def validate_otp(self, value):
        phone = self.initial_data.get('phone')

        if not verify_otp_auth_num(phone, value):
            raise serializers.ValidationError("Invalid OTP provided. Please try again.")
        return value
    

class BaseLoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        super().validate(attrs)
        password = attrs['password']
        user = self.get_user(attrs)

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")
        
        attrs['user'] = user
        return attrs

    def get_user(self, attrs):
        raise NotImplementedError("Subclasses must implement get_user method")


class PhoneLoginSerializer(BaseLoginSerializer):
    phone = PhoneNumberField(max_length=13)

    def get_user(self, attrs):
        phone = attrs['phone']
        return get_object_or_404(User, phone=phone)
