from rest_framework import serializers
from .models import *


class ArticleCategorySerializer(serializers.ModelSerializer):
    parent_slug = serializers.SerializerMethodField()
    childrens = serializers.SerializerMethodField()

    class Meta:
        model = ArticleCategory
        fields = ['name', 'slug', 'parent', 'childrens']

    def get_parent_slug(self, obj):
        return obj.parent.slug if obj.parent else None
    
    def get_childrens(self, obj):
        return ArticleCategorySerializer(obj.childrens, many=True).data