from rest_framework import serializers
from accounts.models import UserProfile, User, EmployeeProfile, SocialLink, Job, Skill
from accounts.serializers import RequestOTPSerializer, VerifyOTPSerializer
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from utils import verify_otp_change_phone
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _



class BaseNameRelatedField(serializers.PrimaryKeyRelatedField):
    model = None
    display_field = 'name'
    
    def to_representation(self, value):
        if not hasattr(value, self.display_field):
            try:
                value = self.model.objects.get(pk=value.pk)
            except ObjectDoesNotExist:
                return None
        return getattr(value, self.display_field)


class SkillRelatedField(BaseNameRelatedField):
    model = Skill
    display_field = 'name'


class JobRelatedField(BaseNameRelatedField):
    model = Job
    display_field = 'name'


class UserProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    first_name = serializers.CharField(source='user.first_name', allow_blank=True)
    last_name = serializers.CharField(source='user.last_name')
    gender = serializers.CharField(source='get_gender_display')
    skills = SkillRelatedField(
        queryset=Skill.objects.filter(is_active=True),
        many=True,
    )
    job = JobRelatedField(
        queryset=Job.objects.filter(is_active=True),
    )

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'bio',
            'job', 'avatar', 'age', 'gender',
            'phone', 'skills',
        ]
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        skills = validated_data.pop('skills', [])
        
        
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        
        if skills:
            instance.skills.set(skills)
        
        return instance


class ChangePhoneRequestSerializer(RequestOTPSerializer):
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(_("این شماره تلفن قبلاً ثبت شده است."))
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
        fields = ('username',)
        
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
            EmployeeProfile,
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


class SkillListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


class JobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'name')
