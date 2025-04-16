from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from taggit.serializers import TagListSerializerField, TaggitSerializer

from accounts.models import User
from courses.models import (
    Course,
    Lesson,
    Season,
    LearningPath,
    CourseCategory,
    Feature,
    FAQ,
)


# region Base
class BaseCourseSerializer(serializers.ModelSerializer):
    banner_thumbnail = serializers.ImageField(read_only=True)
    main_price = serializers.IntegerField(source='price.main_price', read_only=True)
    final_price = serializers.IntegerField(source='price.final_price', read_only=True)

    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'main_price', 'final_price', 'duration',
            'short_description', 'banner_thumbnail',
        )
       
     
class BaseLessonDisplaySerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.slug', read_only=True)

    class Meta:
        model = Lesson
        fields = ('title', 'course', 'description', 'url_video', 'url_files', 'duration')


class BaseSeasonDisplaySerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.slug', read_only=True)
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ('title', 'description','duration', 'course', 'lessons')
    
    def get_lessons(self, obj):
        lessons = Lesson.objects.filter(season=obj, is_deleted=False)
        return BaseLessonDisplaySerializer(lessons, many=True).data
# endregion


# region Teacher
class TeacherSeasonManagementSerializer(serializers.ModelSerializer):
    """
    This serializer allows teachers to effectively manage the seasons of a specific course.
    It supports creating, view a list, editing, and deleting seasons, providing detailed
    information about each season for improved course management.
    """
    
    course_slug = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        model = Season
        fields = ('id', 'title', 'description', 'course_slug', 'is_published', 'order')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        validated_data.pop('is_published')
        course_slug = validated_data.pop('course_slug')
        teacher = self.context['request'].user
        
        course = get_object_or_404(
            Course,
            slug=course_slug,
            teacher=teacher,
            is_deleted=False
        )
        season = Season(**validated_data, course=course)
        
        try:
            season.full_clean()
            season.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        season.course_slug = course_slug
        return season
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['course_slug'] = instance.course.slug
        return representation


class TeacherLessonManagementSerializer(serializers.ModelSerializer):
    """
    This serializer allows teachers to effectively manage lessons within a course.
    It supports creating, editing, deleting, and viewing details of lessons,
    providing essential information for improved course management.
    """
    
    season_id = serializers.IntegerField(required=False)
    course_slug = serializers.CharField(required=True, write_only=True)
    course = serializers.CharField(source='course.slug', read_only=True)
    
    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'description', 'season_id',
            'is_published', 'url_files', 'url_video',
            'course_slug', 'course'
        )
        read_only_fields = ('id', 'course')
        write_only_fields = ('season_id',)
    
    def create(self, validated_data):
        teacher = self.context['request'].user
        validated_data.pop('is_published')
        season_id = validated_data.pop('season_id', None)
        course_slug = validated_data.pop('course_slug')
        
        course = get_object_or_404(
            Course,
            slug=course_slug,
            teacher=teacher,
            is_deleted=False
        )
        
        season = None
        if season_id:
            season = get_object_or_404(
                Season,
                id=season_id,
                course=course,
                is_deleted=False
            )
        
        lesson = Lesson(**validated_data, course=course, season=season)
        
        try:
            lesson.full_clean()
            lesson.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return lesson


class TeacherSeasonDisplaySerializer(BaseSeasonDisplaySerializer):
    class Meta(BaseSeasonDisplaySerializer.Meta):
        fields = BaseSeasonDisplaySerializer.Meta.fields + ('id', 'is_published', 'created_at', 'updated_at')


class TeacherCoursesSerializer(BaseCourseSerializer):
    """
    This serializer is used to display a list of courses created by the specific teacher.
    It allows the teacher to view their own courses.
    """

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + ('count_lessons',)
 

class TeacherLessonDisplaySerializer(BaseLessonDisplaySerializer):
    class Meta(BaseLessonDisplaySerializer.Meta):
        fields = BaseLessonDisplaySerializer.Meta.fields + ('is_published', 'id', 'created_at', 'updated_at')


class TeacherCourseDetailManagementSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Serializer for managing course details by administrators (teachers).
    Supports creating, editing, viewing, and deleting courses.
    Includes fields for title, description, pricing, tags, and categories.
    """
    tags = TagListSerializerField()
    categories = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=CourseCategory.objects.filter(is_active=True)
    )
    learning_path = serializers.SerializerMethodField(read_only=True)
    main_price = serializers.IntegerField(source='price.main_price', read_only=True)
    final_price = serializers.IntegerField(source='price.final_price', read_only=True)
    seasons = TeacherSeasonDisplaySerializer(many=True, read_only=True)
    lessons_no_season = serializers.SerializerMethodField(read_only=True)

    start_level = serializers.IntegerField(required=True, write_only=True)
    end_level = serializers.IntegerField(default=None, write_only=True)
    
    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'description', 'short_description', 'categories',
            'tags', 'start_level', 'end_level', 'banner', 'status', 'language',
            'is_published', 'learning_path', 'start_date', 'url_video',
            'duration', 'created_at', 'updated_at', 'last_lesson_update',
            'main_price', 'final_price', 'count_lessons', 'count_students',
            'has_seasons', 'seasons', 'lessons_no_season', 'prerequisites',
        )
        extra_kwargs = {
            # write_only
            'start_level': {'write_only': True},
            'end_level': {'write_only': True},
            
            # read only
            'duration': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'count_lessons': {'read_only': True},
            'count_students': {'read_only': True},
            'slug': {'read_only': True},
            'main_price': {'read_only': True},
            'final_price': {'read_only': True},
            'learning_path': {'read_only': True},
            'seasons': {'read_only': True},
            'lessons_no_season': {'read_only': True},
        }
        
    def create(self, validated_data):
        validated_data.pop('is_published')
        validated_data.pop('has_seasons')
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

    def get_lessons_no_season(self, obj):
        lessons = Lesson.objects.filter(course=obj, season=None, is_deleted=False)
        return TeacherLessonDisplaySerializer(lessons, many=True).data
    
    def validate_is_published(self, value):
        if value is False:
            if self.instance and self.instance.is_published:
                raise serializers.ValidationError(
                    "امکان تغییر وضعیت از انتشار به عدم انتشار وجود ندارد. "
                )
        return value


class TeacherCoursesSerializer(BaseCourseSerializer):
    """
    This serializer is used to display a list of courses created by the specific teacher.
    It allows the teacher to view their own courses.
    """

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields


class TeacherProfileSerializer(serializers.ModelSerializer):
    """
    This serializer is used to display teacher information in course lists.
    It includes the teacher's full name, username and avatar thumbnail.
    """
    
    avatar_thumbnail = serializers.ImageField(source='profiles.avatar_thumbnail', read_only=True)
    username = serializers.CharField(source='user_profile.employee_profile.username')
    class Meta:
        model = User
        fields = (
            'full_name',
            'avatar_thumbnail',
            'username',
        )


class TeacherFeatureSerializer(serializers.ModelSerializer):
    course_slug = serializers.CharField(required=True, write_only=True)
    class Meta:
        model = Feature
        fields = ('id', 'title', 'description', 'course_slug', 'order')
        
    def create(self, validated_data):
        teacher = self.context['request'].user
        course_slug = validated_data.pop('course_slug')
        
        course = get_object_or_404(Course, slug=course_slug, teacher=teacher)
        
        feature = Feature(**validated_data, course=course)
        
        try:
            feature.full_clean()
            feature.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return feature

class TeacherFAQSerializer(serializers.ModelSerializer):
    course_slug = serializers.CharField(required=True, write_only=True)
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer', 'course_slug', 'order')
        
    def create(self, validated_data):
        teacher = self.context['request'].user
        course_slug = validated_data.pop('course_slug')
        
        course = get_object_or_404(Course, slug=course_slug, teacher=teacher)
        
        faq = FAQ(**validated_data, course=course)
        
        try:
            faq.full_clean()
            faq.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return faq

# endregion


# region User
class UserSeasonDisplaySerializer(BaseSeasonDisplaySerializer):
    lessons = serializers.SerializerMethodField()

    def get_lessons(self, obj):
        lessons = Lesson.objects.filter(season=obj, is_deleted=False, is_published=True)
        return UserLessonDisplaySerializer(lessons, many=True).data


class UsersCourseListSerializer(BaseCourseSerializer):
    """
    This serializer is used to display an overview of all courses for users.
    It includes information about each course and the related teacher's details.
    """
    teacher = serializers.SerializerMethodField()

    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + ('teacher',)
        
    def get_teacher(self, obj):
        return {
            "full_name": f"{obj.teacher_first_name.strip()} {obj.teacher_last_name.strip()}",
            "username": obj.teacher_username,
        }


class UserFeatureListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('title', 'description')


class UserFAQListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('question', 'answer')


class UserCourseDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    # teacher = TeacherProfileSerializer(read_only=True)
    teacher = serializers.SerializerMethodField(read_only=True)
    main_price = serializers.IntegerField(source='price.main_price', read_only=True)
    final_price = serializers.IntegerField(source='price.final_price', read_only=True)
    learning_path = serializers.CharField(source='learning_path.title', read_only=True)
    seasons = serializers.SerializerMethodField(read_only=True)
    lessons = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source='get_status_display')
    language = serializers.CharField(source='get_language_display')
    feature = serializers.SerializerMethodField(read_only=True)
    faq = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'main_price', 'final_price',
            'learning_path', 'short_description', 'description',
            'status', 'count_lessons','teacher', 'banner',
            'start_date', 'tags', 'feature',
            'duration', 'has_seasons', 'seasons',
            'lessons', 'language', 'prerequisites', 'faq',
            'last_lesson_update'
        )
    
    def get_lessons(self, obj):
        if obj.has_seasons:
            return None

        lessons = getattr(obj, 'prefetched_lessons', [])
        return UserLessonDisplaySerializer(lessons, many=True).data

    def get_seasons(self, obj):
        if not obj.has_seasons:
            return None

        seasons = getattr(obj, 'prefetched_seasons', [])
        return UserSeasonDisplaySerializer(seasons, many=True).data
    
    def get_faq(self, obj):
        faqs = getattr(obj, 'prefetched_faqs', [])
        return UserFAQListSerializer(faqs, many=True).data
    
    def get_feature(self, obj):
        features = getattr(obj, 'prefetched_features', [])
        return UserFeatureListSerializer(features, many=True).data

    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not representation.get('has_seasons', False):
            representation.pop('seasons', None)
        else:
            representation.pop('lessons', None)

        return representation
    
    def get_teacher(self, obj):
        return {
            "full_name": f"{obj.teacher_first_name.strip()} {obj.teacher_last_name.strip()}",
            "username": obj.teacher_username,
        }


class CategoryHierarchySerializer(serializers.ModelSerializer):
    """
    This serializer is used to display the hierarchy of all categories,
    including parent and child categories. It helps users understand
    the structure of categories within the system.
    """
    
    children = serializers.SerializerMethodField()
    parent_slug = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = ['title', 'slug', 'parent_slug', 'children']
        
    def get_parent_slug(self, obj):
        return obj.parent.slug if obj.parent else None

    def get_children(self, obj):
        return CategoryHierarchySerializer(obj.get_children(), many=True).data
     

class UserLessonDisplaySerializer(BaseLessonDisplaySerializer):
    pass
# endregion
