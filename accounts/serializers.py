from rest_framework import serializers
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from accounts.models import (
    User,
    EmployeeProfile,
    Skill,
    Job,
    UserProfile,
    SocialLink
)
from utils import (
    verify_otp_auth_num,
    verify_otp_change_phone,
    verify_otp_reset_password,
    BaseNameRelatedField,
)


# region Field

class PhoneNumberField(serializers.CharField):
    default_validators = [
        RegexValidator(
            regex=r'^\+98[0-9]{10}$',
            message="Phone number must be entered in the format: '+9891234567890'. Exactly 12 digits allowed."
        )
    ]


class PasswordField(serializers.CharField):
    default_validators = [
        RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*()\-_=+{}[\]|;:",.<>/?]).{8,}$',
            message=(
                "Password must be at least 8 characters long and include: "
                "1 uppercase letter, 1 lowercase letter, 1 digit, and "
                "1 special character (!@#$ etc.)"
            )
        )
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('style', {'input_type': 'password'})
        super().__init__(required=True, write_only=True, *args, **kwargs)


class SkillRelatedField(BaseNameRelatedField):
    model = Skill
    display_field = 'name'


class JobRelatedField(BaseNameRelatedField):
    model = Job
    display_field = 'name'

# endregion

# region Auth

class RequestOTPSerializer(serializers.Serializer):
    phone = PhoneNumberField(max_length=13)


class VerifyOTPSerializer(serializers.Serializer):
    phone = PhoneNumberField(max_length=13)
    otp = serializers.IntegerField(required=True, write_only=True)

    def validate_otp(self, value):
        phone = self.initial_data.get('phone')

        if not verify_otp_auth_num(phone, value):
            raise serializers.ValidationError("Invalid OTP provided. Please try again.")
        return value
    

class BaseLoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        super().validate(attrs)
        try:
            user = User.objects.get(phone=attrs['phone'])
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError(
                    {"password": _("پسورد اشتباه است")}
                )
            attrs['user'] = user
            return attrs
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {"password": _("پسورد اشتباه است")}
            )

    def get_user(self, attrs):
        raise NotImplementedError("Subclasses must implement get_user method")


class PhoneLoginSerializer(BaseLoginSerializer):
    phone = PhoneNumberField(max_length=13)

    def get_user(self, attrs):
        phone = attrs['phone']
        return get_object_or_404(User, phone=phone)

# endregion

# region Employee and Team

class EmployeeListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = ['username', 'full_name', 'avatar_thumbnail']
    
    def get_full_name(self, obj):
        return obj.user_profile.user.full_name()
    
    def get_avatar_thumbnail(self, obj):
        if obj.user_profile.avatar_thumbnail and hasattr(obj.user_profile.avatar_thumbnail, 'url'):
            return obj.user_profile.avatar_thumbnail.url
        return None


class EmployeeDetailSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='user_profile.user.full_name')
    social_links = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    

    class Meta:
        model = EmployeeProfile
        fields = (
            'full_name', 'bio', 'avatar', 'groups',
            'skills', 'roles', 'social_links'
        )
        
    def get_skills(self, obj):
        skills = obj.user_profile.skills.filter(is_active=True).values_list('name', flat=True)
        return list(skills)
        
    def get_roles(self, obj):
        roles = obj.roles.names()
        return list(roles)
    
    def get_bio(self, obj):
        return str(obj.user_profile.bio)
        
    def get_groups(self, obj):
        group_names = obj.user_profile.user.groups.filter(
            custom_group__is_display=True
        ).values_list('name', flat=True)
        return list(group_names)
    
    def get_social_links(self, obj):
        social_links = obj.social_link.all()
        return [
            {
                "link": social_link.link,
                "type_social": social_link.social_media_type,
            }
            for social_link in social_links
        ]
    
    def get_avatar(self, obj):
        if obj.user_profile.avatar and hasattr(obj.user_profile.avatar, 'url'):
            return obj.user_profile.avatar.url
        return None

# endregion

# region Password

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
        user = get_object_or_404(User, phone=phone)

        if not verify_otp_reset_password(phone, otp):
            raise serializers.ValidationError({'otp': 'Invalid OTP provided. Please try again.'})
        attrs['user'] = user
        return attrs

# endregion

# region Update

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
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(_("این شماره تلفن قبلاً ثبت شده است."))
        return value
    
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

# endregion

# region List(for selected fields)

class SkillListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


class JobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'name')

# endregion
