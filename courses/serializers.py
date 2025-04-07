from rest_framework import serializers
from django.shortcuts import get_object_or_404
from taggit.serializers import TagListSerializerField, TaggitSerializer

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


class BaseCourseSerializer(serializers.ModelSerializer):
    banner_thumbnail = serializers.ImageField(read_only=True)
    main_price = serializers.IntegerField(source='prices.main_price', read_only=True)
    final_price = serializers.IntegerField(source='prices.final_price', read_only=True)

    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'main_price', 'final_price', 'course_duration',
            'short_description', 'banner_thumbnail', 'start_date',
            'status', 'count_lessons',
        )


class CourseByTeacherListSerializer(BaseCourseSerializer):

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields


class CourseListSerializer(BaseCourseSerializer):
    teacher = TeacherDetailSerializer(read_only=True)
    learning_path = serializers.CharField(source='learning_path.title', read_only=True)

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + ('learning_path', 'teacher')


class CourseDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
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
            'course_duration', 'tags',
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


class LearningLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningLevel
        fields = ('name', 'level_number', 'description')


class SeasonSerializer(serializers.ModelSerializer):
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    class Meta:
        model = Season
        fields = ('title', 'description', 'course_slug', 'is_published')
    
    def create(self, validated_data):
        validated_data.pop('is_published')
        season = Season.objects.create(**validated_data)
        return season


class CourseByTeacherSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    categories = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=CourseCategory.objects.filter(is_active=True)
    )
    start_level = serializers.IntegerField(required=True, write_only=True)
    end_level = serializers.IntegerField(write_only=True, default=None)
    learning_path = serializers.SerializerMethodField(read_only=True)
    main_price = serializers.IntegerField(source='prices.main_price', read_only=True)
    final_price = serializers.IntegerField(source='prices.final_price', read_only=True)
    
    class Meta:
        model = Course
        fields = (
            'title', 'description', 'short_description', 'categories',
            'tags', 'start_level', 'end_level', 'banner', 'status',
            'is_published', 'learning_path', 'start_date', 'end_date',
            'course_duration', 'created_at', 'updated_at', 'main_price',
            'final_price', 'count_lessons', 'count_students',
        )
        read_only_fields = (
            'course_duration', 'created_at', 'updated_at',
            'count_lessons', 'count_students',
        )
        
    def create(self, validated_data):
        validated_data.pop('is_published')
        tags = validated_data.pop('tags')
        categories = validated_data.pop('categories')
        start_level = validated_data.pop('start_level')
        end_level = validated_data.pop('end_level')
        
        learning_path = get_object_or_404(
            LearningPath,
            start_level__level_number=start_level,
            end_level__level_number=end_level
        )
        course = Course(**validated_data, learning_path=learning_path)
        
        try:
            course.full_clean()
            course.save()
            course.tags.set(tags)
            course.categories.set(categories)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return course
    
    def get_learning_path(self, obj):
        return obj.learning_path.title() if obj.learning_path else None

