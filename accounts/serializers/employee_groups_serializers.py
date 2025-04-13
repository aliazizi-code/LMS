from rest_framework import serializers
from accounts.models import EmployeeProfile


class TeamSerializer(serializers.ModelSerializer):
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
    position = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='user_profile.user.full_name')
    bio = serializers.CharField(source='user_profile.bio')
    social_links = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    

    class Meta:
        model = EmployeeProfile
        fields = (
            'full_name', 'bio', 'avatar', 'groups',
            'skills', 'position', 'social_links'
        )
        
    def get_skills(self, obj):
        skills = obj.skills.names()
        return list(skills)
        
    def get_position(self, obj):
        position = obj.position.roles.names()
        return list(position)
        
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
