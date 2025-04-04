from rest_framework import serializers

from courses.models import *
from accounts.models import User


class TeacherDetailSerializer(serializers.ModelSerializer):
    avatar_thumbnail = serializers.ImageField(source='profiles.avatar_thumbnail', read_only=True)
    class Meta:
        model = User
        fields = ('id' ,'full_name' ,'avatar_thumbnail')


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ('id' ,'title', 'slug')


class CourseListSerializer(serializers.ModelSerializer):
    banner_thumbnail = serializers.ImageField(read_only=True)
    teacher = TeacherDetailSerializer(read_only=True)
    main_price = serializers.IntegerField(source='prices.main_price', read_only=True)
    final_price = serializers.IntegerField(source='prices.final_price', read_only=True)
    learning_path = serializers.CharField(source='learning_path.title', read_only=True)
    categories = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'main_price', 'final_price', 'course_duration',
            'learning_path' ,'short_description', 'banner_thumbnail', 'start_date',
            'status', 'count_students', 'count_lessons', 'rating', 'categories', 'teacher'
        )
    
    def get_categories(self, obj):
        return CourseCategorySerializer(obj.category.filter(is_active=True), many=True).data


class CourseDetailSerializer(serializers.ModelSerializer):
    teacher = TeacherDetailSerializer(read_only=True)
    main_price = serializers.IntegerField(source='prices.main_price', read_only=True)
    final_price = serializers.IntegerField(source='prices.final_price', read_only=True)
    learning_path = serializers.CharField(source='learning_path.title', read_only=True)
    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'main_price', 'final_price',
            'learning_path', 'description', 'status',
            'count_students', 'count_lessons', 'rating',
            'teacher', 'banner', 'start_date', 'end_date',
            'course_duration', 
        )


class CategoryWithChildrenSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = ['title', 'slug', 'parent_slug', 'children']
        
    def get_parent_slug(self, obj):
        return obj.parent.slug if obj.parent else None

    def get_children(self, obj):
        return CategoryWithChildrenSerializer(obj.get_children(), many=True).data




