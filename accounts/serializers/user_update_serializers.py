from rest_framework import serializers
from accounts.models import UserProfile, User, EmployeeProfile, SocialLink
from accounts.serializers import RequestOTPSerializer, VerifyOTPSerializer
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from utils import verify_otp_change_phone
from taggit.serializers import TagListSerializerField, TaggitSerializer


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


class EmployeeProfileSerializer(TaggitSerializer, serializers.ModelSerializer):
    skills = TagListSerializerField()
    
    class Meta:
        model = EmployeeProfile
        fields = ('username', 'skills')
        
    def create(self, validated_data):
        user = self.context['request'].user
        skills = validated_data.pop('skills', [])
        
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        
        employee_profile = EmployeeProfile(
            user_profile=user_profile,
            **validated_data
        )
        
        try:
            employee_profile.full_clean()
            employee_profile.save()
            
            if skills:
                employee_profile.skills.set(skills)
            
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return employee_profile
 
 
class EmployeeSocialLinkSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='employee_profile.username', read_only=True)
    class Meta:
        model = SocialLink
        fields = ('link', 'social_media_type', 'username')
        
    def create(self, validated_data):
        user = self.context['request'].user
        employee_profile = get_object_or_404(EmployeeProfile, user=user)
        
        social_link = SocialLink(
            employee_profile=employee_profile,
            **validated_data
        )
        
        try:
            social_link.full_clean()
            social_link.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return social_link
