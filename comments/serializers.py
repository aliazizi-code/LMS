from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user_avatar = serializers.ImageField(source='user.user_profile.avatar_thumbnail', read_only=True)
    user = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    model_type = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        model = Comment
        fields = (
            'id' , 'user', 'text','parent',
            'created_at', 'user_avatar',
            'replies',
            'model_type', 'object_slug'
        )
        extra_kwargs = {
            'object_slug': {'write_only': True},
        }
    
    def get_replies(self, obj):
        replies = getattr(obj, 'prefetched_replies', [])
        return CommentSerializer(replies, many=True).data
    
    def get_user(self, obj):
        first_name = obj.user.first_name or ''
        last_name = obj.user.last_name or ''
        
        full_name = f"{first_name} {last_name}".strip()
        return full_name if len(full_name) > 1 else 'کاربر سایت'
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        content_type = validated_data.pop('model_type', None)
        
        if not user.is_authenticated:
            raise NotAuthenticated((_("اطلاعات برای اعتبارسنجی ارسال نشده است.")))
        
        content_type = get_object_or_404(ContentType, model=content_type)
        
        
        comment = Comment(
            **validated_data,
            user=user,
            content_type=content_type
        )
        
        try:
            comment.full_clean()
            comment.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return comment
