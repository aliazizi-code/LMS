from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.urls import path

from . import models
from mptt.admin import DraggableMPTTAdmin


class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'display_price', 'status',
        'is_published', 'is_deleted', 'thumbnail',
    )
    readonly_fields = (
        'slug', 'created_at', 'updated_at', 'display_price',
        'count_students', 'count_lessons', 'thumbnail',
        'course_duration', 'sv'
    )
    list_filter = (
        'status', 'is_published', 'is_deleted', 'teacher',
        'categories', 'start_date', 'end_date', 'learning_path',
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
                'tags', 'categories', 'learning_path', 'course_duration',
            ),
        }),
        ('رسانه', {
            'fields': ('banner', 'thumbnail', 'url_video'),
        }),
        ('وضعیت', {
            'fields': ('status', 'is_published', 'is_deleted', 'has_seasons'),
        }),
        ('اطلاعات قیمت', {
            'fields': ('display_price',),
        }),
        ('آمار', {
            'fields': ('count_students', 'count_lessons'),
        }),
        ('اطلاعات اضافی', {
            'fields': ('teacher', 'start_date', 'end_date', 'created_at', 'updated_at'),
        }),
        (None, {
            'fields' : ('sv',)
        })
    )

    def display_price(self, obj):
        return f"{obj.prices.final_price:,.0f}" if hasattr(obj, 'prices') else "No Price"

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


class PriceAdmin(admin.ModelAdmin):
    list_display = (
    'course', 'formatted_main_price', 'formatted_discount_percentage', 'formatted_final_price', 'discount_expires_at')
    search_fields = ('course__title',)
    list_filter = ('discount_percentage',)
    readonly_fields = ('final_price',)

    def formatted_main_price(self, obj):
        return f"{obj.main_price:,.0f}"

    formatted_main_price.short_description = "Main Price"

    def formatted_final_price(self, obj):
        return f"{obj.final_price:,.0f}"

    formatted_final_price.short_description = "Final Price"

    def formatted_discount_percentage(self, obj):
        return f"{obj.discount_percentage}%"

    formatted_discount_percentage.short_description = "Discount Percentage"

    def reset_discount(self, request, queryset):
        for price in queryset:
            price.discount_percentage = 0
            price.final_price = price.main_price
            price.save()
        self.message_user(request, "Discounts have been reset.")

    reset_discount.short_description = "Reset discounts for selected prices"

    actions = [reset_discount]


class CourseCategoryAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions",'indented_title', 'is_active')
    autocomplete_fields = ('parent',)
    readonly_fields = ('created_at',)
    list_filter = ('is_active',)
    search_fields = ('title',)


class SeasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'is_published', 'is_deleted')
    search_fields = ('title',)
    list_filter = ('is_published', 'course', 'is_deleted')
    autocomplete_fields = ('course',)
    readonly_fields = ('id', 'season_duration', 'course_slug', 'course_id')
    
    fieldsets = (
        (None, {
            'fields': (
                'id', 'course_slug', 'course_id',
                'title', 'description', 'season_duration',
                'course', 'is_published', 'is_deleted',
            )
        }),
    )
    
    def course_slug(self, obj):
        return obj.course.slug if obj.course else None
    
    def course_id(self, obj):
        if obj.course:
            url = reverse('admin:courses_course_change', args=[obj.course.id])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.course.id)
        return None


    course_id.short_description = "Course ID"
    course_slug.short_description = "Course Slug"


admin.site.register(models.Course, CourseAdmin)
admin.site.register(models.Price, PriceAdmin)
admin.site.register(models.Season, SeasonAdmin)
admin.site.register(models.Lesson)
admin.site.register(models.CourseCategory, CourseCategoryAdmin)
admin.site.register(models.LearningLevel)
admin.site.register(models.LearningPath)
