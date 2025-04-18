from rest_framework import serializers
from accounts.models import UserProfile, User, EmployeeProfile, SocialLink, Job
from accounts.serializers import RequestOTPSerializer, VerifyOTPSerializer
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from utils import verify_otp_change_phone
from taggit.serializers import TagListSerializerField, TaggitSerializer


class UserProfileSerializer(TaggitSerializer, serializers.ModelSerializer):
    skills = TagListSerializerField()
    phone = serializers.CharField(source='user.phone', read_only=True)
    first_name = serializers.CharField(source='user.first_name', allow_blank=True)
    last_name = serializers.CharField(source='user.last_name')
    job_name = serializers.CharField(source='job.title', read_only=True)
    gender = serializers.CharField(source='get_gender_display')
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        source='job',
        write_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name',
            'job_id', 'job_name', 'avatar',
            'age', 'gender', 'phone', 'skills'
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
            raise serializers.ValidationError("این شماره تلفن قبلاً ثبت شده است.")
        return value
          
        
class ChangePhoneVerifySerializer(VerifyOTPSerializer):
    def validate_otp(self, value):
        phone = self.initial_data.get('phone')

        if not verify_otp_change_phone(phone, value):
            raise serializers.ValidationError("کد تأیید وارد شده نامعتبر است. لطفاً مجدداً تلاش کنید.")
        return value


class EmployeeProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = EmployeeProfile
        fields = ('username', 'bio')
        
    def create(self, validated_data):
        user = self.context['request'].user
        
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        
        employee_profile = EmployeeProfile(
            user_profile=user_profile,
            **validated_data
        )
        
        try:
            employee_profile.full_clean()
            employee_profile.save()
            
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return employee_profile
 
 
class EmployeeSocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ('link', 'social_media_type')
        
    def create(self, validated_data):
        user = self.context['request'].user
        employee_profile = get_object_or_404(
            EmployeeProfile.objects.select_related(
                'user_profile__user'
            ).only(
                'id', 'user_profile__user__id'
            ),
            user_profile__user=user
        )
        
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
