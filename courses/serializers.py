from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from utils import BaseNameRelatedField
from courses.models import (
    Course,
    Lesson,
    Season, 
    LearningLevel,
    CourseCategory,
    Feature,
    FAQ,
    LessonMedia,
    CourseRequest,
)


class CourseRelatedField(BaseNameRelatedField):
    model = Course
    display_field = 'title'


# region Teacher
class TeacherCourseListSerializer(serializers.ModelSerializer):
    banner_thumbnail = serializers.ImageField(read_only=True)
    class Meta:
        model = Course
        fields = (
            'id' ,'title', 'slug', 'short_description',
            'banner_thumbnail', 'duration', 'is_published',
        )


class TeacherCourseDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    categories = serializers.SerializerMethodField()
    learning_path = serializers.CharField(source='learning_path.title', read_only=True)
    language = serializers.CharField(source='get_language_display')
    status = serializers.CharField(source='get_status_display')
    
    class Meta:
        model = Course
        fields = (
            'id' ,'title', 'slug', 'description', 'short_description',
            'categories', 'tags', 'language', 'prerequisites',
            'learning_path', 'banner', 'url_video', 'status',
            'count_lessons', 'duration', 'is_published',
            'has_seasons', 'start_date', 'last_lesson_update',
            'published_at',
        )
        
    def get_categories(self, obj: Course):
        return list(obj.categories.values("title", "slug"))


class TeacherSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ('id', 'title', 'order', 'duration')


class TeacherLessonSerializer(serializers.ModelSerializer):
    season = serializers.SerializerMethodField()
    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'order', 'duration',
            'url_video', 'url_attachment', 'season',
            'is_published', 'published_at',
        )
        
    def get_season(self, obj: Lesson):
        if obj.season:
            return {
                "id": obj.season.id,
                "title": obj.season.title
            }
        return None


class TeacherFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'title', 'order', 'description',)


class TeacherFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'order', 'answer',)


class TeacherUploadMediaSerializer(serializers.ModelSerializer):
    course = CourseRelatedField(
        queryset=Course.objects.exclude(status='CANCELLED').filter(is_deleted=False)
    )
    course_id = serializers.IntegerField(source='course.pk', read_only=True)
    class Meta:
        model = LessonMedia
        fields = ('course_id' ,'course', 'video', 'attachment')
        
    def create(self, validated_data):
        user = self.context['request'].user
        
        lesson_media = LessonMedia(**validated_data, uploaded_by=user)
        
        try:
            lesson_media.full_clean()
            lesson_media.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return lesson_media


class TeacherCourseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRequest
        fields = (
            'id', 'target_type', 'target_id', 'action',
            'status', 'comments', 'admin_response',
            'data',
        )
        extra_kwargs = {
            'status': {'read_only': True},
            'admin_response': {'read_only': True},
        }
        
    def create(self, validated_data):
        user = self.context['request'].user
        
        course_request = CourseRequest(**validated_data, teacher=user)
        
        try:
            course_request.full_clean()
            course_request.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        return course_request
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['action'] = instance.get_action_display()
        representation['status'] = instance.get_status_display()
        representation['target_type'] = instance.get_target_type_display()
        return representation

# endregion


# region General

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
        children = getattr(obj, 'prefetched_children', [])
        return CategoryHierarchySerializer(children, many=True).data


class LearningLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningLevel
        fields = ('name', 'level_number')


class CourseListSerializer(serializers.ModelSerializer):
    """
    This serializer is used to display an overview of all courses for users.
    It includes information about each course and the related teacher's details.
    """
    
    banner_thumbnail = serializers.ImageField(read_only=True)
    main_price = serializers.IntegerField(source='price.main_price', read_only=True)
    final_price = serializers.IntegerField(source='price.final_price', read_only=True)
    teacher = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Course
        fields =(
            'title', 'slug', 'main_price', 'final_price', 'duration',
            'short_description', 'banner_thumbnail', 'status', 'teacher',
        )
        
    def get_teacher(self, obj):
        return {
            "full_name": f"{obj.teacher_first_name.strip()} {obj.teacher_last_name.strip()}",
            "username": obj.teacher_username,
        }
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not instance.status == 'UPCOMING':
            representation.pop('status', None)

        return representation


class CourseDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
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
            'last_lesson_update', 'url_video'
        )
    
    def get_lessons(self, obj):
        if obj.has_seasons:
            return None
        
        lessons = getattr(obj, 'prefetched_lessons', [])
        return [
            {
                "title": lesson.title,
                "duration": lesson.duration,
                "url_video": lesson.url_video,
                "url_attachment": lesson.url_attachment,
            }
            for lesson in lessons
        ]


    def get_seasons(self, obj):
        if not obj.has_seasons:
            return None

        lessons_by_season = {}
        for lesson in getattr(obj, 'prefetched_lessons', []):
            if lesson.season_id not in lessons_by_season:
                lessons_by_season[lesson.season_id] = []
            lessons_by_season[lesson.season_id].append({
                "title": lesson.title,
                "duration": lesson.duration,
                "url_video": lesson.url_video,
            })

        seasons = []
        for season in getattr(obj, 'prefetched_seasons', []):
            seasons.append({
                "title": season.title,
                "lessons": lessons_by_season.get(season.id, [])
            })

        return seasons

    
    def get_faq(self, obj):
        faqs = getattr(obj, 'prefetched_faqs', [])
        return [
            {
                "question": faq.question,
                "answer": faq.answer,
            }
            for faq in faqs
        ]
    
    def get_feature(self, obj):
        features = getattr(obj, 'prefetched_features', [])
        return [
            {
                "title": feature.title,
                "description": feature.description,
            }
            for feature in features
        ]

    
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

# endregion
