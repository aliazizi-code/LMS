from rest_framework import serializers
from .models import *
from taggit.serializers import TagListSerializerField, TaggitSerializer


class ArticleCategorySerializer(serializers.ModelSerializer):
    parent_slug = serializers.SerializerMethodField()
    childrens = serializers.SerializerMethodField()

    class Meta:
        model = ArticleCategory
        fields = ['name', 'slug', 'parent_slug', 'childrens']

    def get_parent_slug(self, obj):
        return obj.parent.slug if obj.parent else None
    
    def get_childrens(self, obj):
        return ArticleCategorySerializer(obj.childrens, many=True).data
    

class ArticleSerializer(TaggitSerializer, serializers.ModelSerializer):
    image_thumbnail = serializers.ImageField(read_only=True)
    tags = TagListSerializerField()
    category = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=ArticleCategory.objects.filter(is_active=True)
    )
    status = serializers.ChoiceField(choices=Article.STATUS.choices,default=Article.STATUS.IN_REVIEW, read_only=True)

    class Meta:
        model = Article
        fields = (
            'author','title', 'slug', 'image', 'image_thumbnail',
            'category', 'content', 'short_description', 'tags',
            'status', 'created_at', 'updated_at', 'published_at',
        )
