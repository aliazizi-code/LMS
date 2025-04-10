from rest_framework import serializers
from accounts.models import UserProfile
from django.contrib.auth.models import Group


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['name', 'members']

    def get_members(self, obj):
        user_profiles = UserProfile.objects.filter(
            user__groups=obj,
            user__first_name__isnull=False,
            user__last_name__isnull=False,
            bio__isnull=False,
            job__isnull=False,
            avatar__isnull=False,
            age__isnull=False,
            gender__isnull=False,
            employee_profile__username__isnull=False,
            employee_profile__social_link__isnull=False,
        ).select_related(
            'employee_profile', 'user'
        ).only(
            'avatar', 
            'user__first_name', 
            'user__last_name',
            'employee_profile__username'
        )
        
        return [
            {
                "full_name": f"{profile.user.first_name} {profile.user.last_name}",
                "username": profile.employee_profile.username,
                "avatar_thumbnail": profile.avatar_thumbnail.url,
            }
            for profile in user_profiles
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='user.full_name')
    position = serializers.CharField(source='employee_profile.position')
    skills = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    

    class Meta:
        model = UserProfile
        fields = (
            'full_name', 'avatar', 'bio',
            'job', 'gender', 'age', 'position',
            'skills', 'social_links', 'groups', 
        )
        
    def get_groups(self, obj):
        group_names = obj.user.groups.filter(
            custom_groups__is_display=True
        ).values_list('name', flat=True)
        return list(group_names)
    
    def get_skills(self, obj):
        skills = obj.employee_profile.skills.all().values_list('name', flat=True)
        return list(skills)
    
    def get_social_links(self, obj):
        social_links = obj.employee_profile.social_link.all()
        return [
            {
                "link": social_link.link,
                "type": social_link.social_media_type,
            }
            for social_link in social_links
        ]
