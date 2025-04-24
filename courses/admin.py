import json
import textwrap
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin
from simple_history.admin import SimpleHistoryAdmin
from deepdiff import DeepDiff

from . import models
from .forms import CourseRequestForm
from .serializers import CourseDetailSerializer


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
            'fields': ('course', 'title', 'description', 'is_deleted')
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
                'tags', 'categories', 'learning_path', 'language',
                'duration',
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
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'parent', 'is_active', 'created_at', 'updated_at')}),
    )


class SeasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'is_deleted')
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    list_filter = ('course', 'is_deleted')
    autocomplete_fields = ('course',)
    readonly_fields = ('id', 'duration', 'course_slug', 'course_id', 'created_at', 'updated_at')
    actions = ['deleted_season', 'undeleted_season']
    
    fieldsets = (
        (None, {
            'fields': (
                'id', 'course_slug', 'course_id',
                'title', 'duration', 'course',
                'order', 'is_deleted',
                'created_at', 'updated_at',
            )
        }),
    )
        
    def deleted_season(self, request, queryset):
        queryset.update(is_deleted=True)
        self.message_user(request, _("Selected season have been deleted."))

    def undeleted_season(self, request, queryset):
        queryset.update(is_deleted=False)
        self.message_user(request, "Selected season have been undeleted.")
    
    def course_slug(self, obj):
        return obj.course.slug if obj.course else None

    course_slug.short_description = "Course Slug"
    deleted_season.short_description = _("Deleted selected season")
    undeleted_season.short_description = _("Undeleted selected season")


class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'is_published', 'is_deleted')
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    list_filter = ('is_published', 'course', 'is_deleted')
    autocomplete_fields = ('course',)
    readonly_fields = ('id', 'duration', 'course_slug', 'course_id', 'created_at', 'updated_at', 'published_at')
    actions = ['publish_lesson', 'unpublish_lesson', 'deleted_lesson', 'undeleted_lesson']
    
    fieldsets = (
        (None, {
            'fields': (
                'id', 'course_slug', 'course_id',
                'title', 'duration',
                'url_video', 'url_attachment',
                'course', 'order', 'season',
                'is_published', 'is_deleted',
                'created_at', 'updated_at', 'published_at'
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


class CourseRequestAdmin(SimpleHistoryAdmin):
    form = CourseRequestForm
    readonly_fields = (
        'api_data_comparison', 'formatted_api_output',
        'admin', 'created_at', 'updated_at', 'teacher'
    )
    
    def formatted_api_output(self, obj):
        api_data = {
            "title": "درک عمیق مفاهیم API از صفر مطلق",
            "slug": "درک-عمیق-مفاهیم-api-از-صفر-مطلق",
            "main_price": None,
            "final_price": None,
            "duration": "00:00:00",
            # "short_description": "تو این دوره، دانشجو ها با مفاهیم پایه و اساسی API آشنا میشن و روش های مختلف استفاده از اون رو یاد میگیرن. همینطور مفاهیمی مثل انواع API ها، نکات پیشرفته api نویسی و.. مورد بررسی قرار میگیرن",
            "banner_thumbnail": "http://localhost:8000/media/CACHE/images/Course/banner/%D8%AF%D8%B1%DA%A9-%D8%B9%D9%85%DB%8C%D9%82-%D9%85%D9%81%D8%A7%D9%87%DB%8C%D9%85-api-%D8%A7%D8%B2-%D8%B5%D9%81%D8%B1-%D9%85%D8%B7%D9%84%D9%82/f6302e507135be1654be3fba2909ed8b.jpg",
            "teacher": {
                "full_name": "مدرس خانواده مدرس",
                "username": "username-1"
            }
        }
        formatted_json = json.dumps(api_data, indent=4, ensure_ascii=False)

        return format_html(
            '''
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
                <script>hljs.highlightAll();</script>

                <div style="direction: ltr; font-family: monospace;">
                    <h3 style="color: #569cd6; font-family: sans-serif;">خروجی API (سریالایزر):</h3>
                    <div style="
                        background-color: #1e1e1e;
                        border-radius: 8px;
                        padding: 15px;
                        width: 800px;
                        max-height: 500px;
                        min-height: 200px;
                        overflow: auto;
                        white-space: pre-wrap;
                        word-break: break-all;
                        overflow-wrap: anywhere;
                    ">
                        <pre style="margin: 0;"><code class="language-json">{}</code></pre>
                    </div>
                </div>
            ''',
            formatted_json
        )

    formatted_api_output.short_description = "خروجی API"
    
    def api_data_comparison(self, obj):
        try:
            api_data = {
                "title": "درک عمیق مفاهیم API از صفر مطلق",
                "slug": "درک-عمیق-مفاهیم-api-از-صفر-مطلق",
                "main_price": None,
                "final_price": None,
                "duration": "00:00:00",
                "short_description": "تو این دوره، دانشجو ها با مفاهیم پایه و اساسی API آشنا میشن و روش های مختلف استفاده از اون رو یاد میگیرن. همینطور مفاهیمی مثل انواع API ها، نکات پیشرفته api نویسی و.. مورد بررسی قرار میگیرن",
                "banner_thumbnail": "http://localhost:8000/media/CACHE/images/Course/banner/%D8%AF%D8%B1%DA%A9-%D8%B9%D9%85%DB%8C%D9%82-%D9%85%D9%81%D8%A7%D9%87%DB%8C%D9%85-api-%D8%A7%D8%B2-%D8%B5%D9%81%D8%B1-%D9%85%D8%B7%D9%84%D9%82/f6302e507135be1654be3fba2909ed8b.jpg",
                "teacher": {
                    "full_name": "مدرس خانواده مدرس",
                    "username": "username-1"
                }
            }
            # model_data = json.loads(obj.data) if obj.data else {}
            model_data = obj.data if isinstance(obj.data, dict) else json.loads(obj.data)
            
            for field in ['id', 'created_at', 'updated_at']:
                api_data.pop(field, None)
                model_data.pop(field, None)
            
            diff = DeepDiff(
                api_data,
                model_data,
                ignore_order=True,
                verbose_level=1,
                exclude_paths=[
                    "root['metadata']",
                    "root['extra_info']"
                ]
            )
            
            result = ['<div style="font-family: Vazir; direction: rtl;">']
            
            if not diff:
                result.append('<div style="color: green; background: #e8f5e9; padding: 10px; border-radius: 5px;">'
                            '✅ فیلد data دقیقاً مطابق با خروجی API است'
                            '</div>')
            else:
                result.append('<div style="color: #d32f2f; background: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 15px;">'
                            '⚠️ تفاوت‌های بین خروجی API و فیلد data:'
                            '</div>')
                
                if 'values_changed' in diff:
                    result.append('<h4>مقادیر متفاوت:</h4>'
                                '<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">'
                                '<tr style="background: #f5f5f5;">'
                                '<th style="padding: 8px; border: 1px solid #ddd;">فیلد</th>'
                                '<th style="padding: 8px; border: 1px solid #ddd;">مقدار در API</th>'
                                '<th style="padding: 8px; border: 1px solid #ddd;">مقدار در data</th>'
                                '</tr>')
                    
                    for path, changes in diff['values_changed'].items():
                        field_name = path.split('root[')[-1].rstrip(']').replace("'", "")
                        result.append(f'''
                        <tr style="border: 1px solid #ddd;">
                            <td style="padding: 8px; border: 1px solid #ddd;"><b>{field_name}</b></td>
                            <td style="padding: 8px; border: 1px solid #ddd; color: #1976D2;">{changes["old_value"]}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; color: #388E3C;">{changes["new_value"]}</td>
                        </tr>
                        ''')
                    result.append('</table>')
                
                if 'dictionary_item_added' in diff:
                    result.append('<div style="background: #fff8e1; padding: 10px; border-radius: 5px; margin-bottom: 10px;">'
                                '<h4>فیلدهای اضافه شده در data:</h4><ul>')
                    for item in diff['dictionary_item_added']:
                        field_name = item.split('root[')[-1].rstrip(']').replace("'", "")
                        result.append(f'<li>{field_name}</li>')
                    result.append('</ul></div>')
                
                if 'dictionary_item_removed' in diff:
                    result.append('<div style="background: #fbe9e7; padding: 10px; border-radius: 5px;">'
                                '<h4>فیلدهای موجود در API ولی отсутствует در data:</h4><ul>')
                    for item in diff['dictionary_item_removed']:
                        field_name = item.split('root[')[-1].rstrip(']').replace("'", "")
                        result.append(f'<li>{field_name}</li>')
                    result.append('</ul></div>')
            
            result.append('</div>')
            return format_html(''.join(result))
        
        except Exception as e:
            return format_html(
                '<div style="color: red; font-family: Vazir;">'
                'خطا در مقایسه: {}'
                '</div>',
                str(e)
            )
    
    api_data_comparison.short_description = "مقایسه API و فیلد data"
    api_data_comparison.allow_tags = True

    fieldsets = (
        (None, {
            'fields': ['target_type', 'target_id', 'action', 'status', 'teacher', 'admin']
        }),
        ('اطلاعات درخواست و داده‌ها', {
            'fields': ['admin_response', 'comments'],
            'classes': ['collapse', 'wide'],
        }),
        ('تاریخچه', {
            'fields': ['created_at', 'updated_at'],
        }),
        ('مقایسه API و داده‌ها', {
            'fields': [
                # 'formatted_api_output',
                # 'api_data_comparison',
                'data'
            ],
            'classes': ['collapse', 'wide'],
        }),
    )


    class Media:
        css = {
            'all': [
                'https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css',
            ]
        }


admin.site.register(models.Course, CourseAdmin)
admin.site.register(models.Season, SeasonAdmin)
admin.site.register(models.Lesson, LessonAdmin)
admin.site.register(models.FAQ, FAQAdmin)
admin.site.register(models.Feature, FeatureAdmin)
admin.site.register(models.CourseCategory, CourseCategoryAdmin)
admin.site.register(models.LearningPath)
admin.site.register(models.LearningLevel)
admin.site.register(models.Price)
admin.site.register(models.LessonMedia)
admin.site.register(models.CourseRequest, CourseRequestAdmin)
