from rest_framework import serializers
from accounts.models import UserProfile
from django.contrib.auth.models import Group


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name')
    class Meta:
        model = UserProfile
        fields = ['full_name', 'avatar']


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['name', 'members']

    def get_members(self, obj):
        members = []
        for user in obj.user_set.all():
            try:
                user_profile = UserProfile.objects.get(user=user)
                employee_profile = user_profile.employee_profile
                members.append({
                    "full_name": user_profile.user.full_name(),
                    "avatar_thumbnail": user_profile.avatar_thumbnail.url if user_profile.avatar else None,
                    "username": employee_profile.username,
                })
            except UserProfile.DoesNotExist:
                members.append({
                    "full_name": user.full_name(),
                    "avatar_thumbnail": None
                })
        return members