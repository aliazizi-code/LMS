from rest_framework import serializers
from accounts.models import UserProfile, User
from accounts.serializers import RequestOTPSerializer, VerifyOTPSerializer
from utils import verify_otp_change_phone


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_thumbnail = serializers.ImageField(read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', allow_blank=True)
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name','bio',
            'job', 'avatar', 'avatar_thumbnail',
            'age', 'gender', 'phone', 'email'
        ]
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class ChangePhoneRequestSerializer(RequestOTPSerializer):
    def validate_phone(self, value):

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value
          
        
class ChangePhoneVerifySerializer(VerifyOTPSerializer):
    def validate_otp(self, value):
        phone = self.initial_data.get('phone')

        if not verify_otp_change_phone(phone, value):
            raise serializers.ValidationError("Invalid OTP provided. Please try again.")
        return value
