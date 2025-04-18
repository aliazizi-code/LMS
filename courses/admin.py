from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from . import models
from mptt.admin import DraggableMPTTAdmin


class FeatureInline(admin.TabularInline):
    model = models.Feature
    extra = 1
    fields = ['title', 'description']
    verbose_name = 'ویژگی'
    verbose_name_plural = 'ویژگی‌های دوره'
    classes = ['collapse']


class FeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course')
    list_display_links = ('id', 'title')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('course', 'title', 'description')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


class FAQInline(admin.TabularInline):
    model = models.FAQ
    extra = 1
    fields = ['question', 'answer']
    verbose_name = 'سوال متداول'
    verbose_name_plural = 'سوالات متداول'
    classes = ['collapse']


class FAQAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'course')
    list_display_links = ('id', 'question')
    list_filter = ('course', 'created_at')
    search_fields = ('question', 'answer', 'course__title')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('course', 'question', 'answer')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    

class PriceInline(admin.StackedInline):
    model = models.Price
    extra = 1
    readonly_fields = ('final_price',)
    classes = ['collapse']


class CourseAdmin(admin.ModelAdmin):
    inlines = [FeatureInline, FAQInline, PriceInline]
    list_display = (
        'title', 'display_price', 'status',
        'is_published', 'is_deleted', 'thumbnail',
    )
    readonly_fields = (
        'slug', 'created_at', 'updated_at', 'display_price',
        'count_students', 'count_lessons', 'thumbnail',
        'duration', 'sv', 'last_lesson_update', 'published_at'
    )
    list_filter = (
        'status', 'is_published', 'is_deleted', 'teacher',
        'categories', 'start_date', 'learning_path',
    )
    search_fields = ('title', 'description', 'short_description', 'tags')
    autocomplete_fields = ('teacher',)
    filter_horizontal = ('categories',)
    ordering = ('-created_at',)
    actions = ['publish_courses', 'unpublish_courses']
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': (
                'title', 'slug', 'description', 'short_description',
                'tags', 'categories', 'learning_path', 'duration',
            ),
        }),
        ('رسانه', {
            'fields': ('banner', 'thumbnail', 'url_video'),
            'classes': ('collapse',)
        }),
        ('وضعیت', {
            'fields': ('status', 'is_published', 'is_deleted', 'has_seasons'),
            'classes': ('collapse',)
        }),
        ('اطلاعات قیمت', {
            'fields': ('display_price',),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('count_students', 'count_lessons'),
            'classes': ('collapse',)
        }),
        ('اطلاعات اضافی', {
            'fields': ('teacher', 'start_date', 'created_at', 'updated_at', 'published_at', 'last_lesson_update'),
            'classes': ('collapse',)
        }),
        ('محتوای سرچ', {
            'fields' : ('sv',),
            'classes': ('collapse',)
        })
    )

    def display_price(self, obj):
        return f"{obj.price.final_price:,.0f}" if hasattr(obj, 'price') else "No Price"

    def publish_courses(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, _("Selected courses have been published."))

    def unpublish_courses(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, "Selected courses have been unpublished.")
    
    def thumbnail(self, obj):
        if obj.banner:
            return format_html(f'<img src="{obj.banner.url}" style="width: 100px; height: auto;" />')
        return "No Image"
    
    display_price.short_description = "Price"
    publish_courses.short_description = _("Publish selected courses")
    unpublish_courses.short_description = _("Unpublish selected courses")
    thumbnail.short_description = "Thumbnail"


class CourseCategoryAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions",'indented_title', 'is_active')
    autocomplete_fields = ('parent',)
    readonly_fields = ('created_at',)
    list_filter = ('is_active',)
    search_fields = ('title',)


class SeasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'is_published', 'is_deleted')
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    list_filter = ('is_published', 'course', 'is_deleted')
    autocomplete_fields = ('course',)
    readonly_fields = ('id', 'duration', 'course_slug', 'course_id')
    actions = ['publish_season', 'unpublish_season', 'deleted_season', 'undeleted_season']
    
    fieldsets = (
        (None, {
            'fields': (
                'id', 'course_slug', 'course_id',
                'title', 'description', 'duration',
                'course', 'order', 'is_published', 'is_deleted',
            )
        }),
    )
    
    def publish_season(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, _("Selected season have been published."))

    def unpublish_season(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, "Selected season have been unpublished.")
        
    def deleted_season(self, request, queryset):
        queryset.update(is_deleted=True)
        self.message_user(request, _("Selected season have been deleted."))

    def undeleted_season(self, request, queryset):
        queryset.update(is_deleted=False)
        self.message_user(request, "Selected season have been undeleted.")
    
    def course_slug(self, obj):
        return obj.course.slug if obj.course else None

    course_slug.short_description = "Course Slug"
    publish_season.short_description = _("Publish selected season")
    unpublish_season.short_description = _("Unpublish selected season")
    deleted_season.short_description = _("Deleted selected season")
    undeleted_season.short_description = _("Undeleted selected season")


class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'is_published', 'is_deleted')
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    list_filter = ('is_published', 'course', 'is_deleted')
    autocomplete_fields = ('course',)
    readonly_fields = ('id', 'duration', 'course_slug', 'course_id')
    actions = ['publish_lesson', 'unpublish_lesson', 'deleted_lesson', 'undeleted_lesson']
    
    fieldsets = (
        (None, {
            'fields': (
                'id', 'course_slug', 'course_id',
                'title', 'description', 'duration',
                'course', 'order', 'season', 'is_published', 'is_deleted',
            )
        }),
    )
    
    def publish_lesson(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, _("Selected lesson have been published."))

    def unpublish_lesson(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, "Selected lesson have been unpublished.")
        
    def deleted_lesson(self, request, queryset):
        queryset.update(is_deleted=True)
        self.message_user(request, _("Selected lesson have been deleted."))

    def undeleted_lesson(self, request, queryset):
        queryset.update(is_deleted=False)
        self.message_user(request, "Selected lesson have been undeleted.")
    
    def course_slug(self, obj):
        return obj.course.slug if obj.course else None

    course_slug.short_description = "Course Slug"
    publish_lesson.short_description = _("Publish selected lesson")
    unpublish_lesson.short_description = _("Unpublish selected lesson")
    deleted_lesson.short_description = _("Deleted selected lesson")
    undeleted_lesson.short_description = _("Undeleted selected lesson")


admin.site.register(models.Course, CourseAdmin)
admin.site.register(models.Season, SeasonAdmin)
admin.site.register(models.Lesson, LessonAdmin)
admin.site.register(models.FAQ, FAQAdmin)
admin.site.register(models.Feature, FeatureAdmin)
admin.site.register(models.CourseCategory, CourseCategoryAdmin)
admin.site.register(models.LearningPath)
admin.site.register(models.LearningLevel)
