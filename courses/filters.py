from django_filters import rest_framework as filters
from .models import Course, CourseCategory
from django.db.models import Q


class CourseFilter(filters.FilterSet):
    order_by = filters.OrderingFilter(
        fields=(
            ('prices__final_price', 'price'),
            ('created_at', 'created'),
        )
    )
    is_free = filters.BooleanFilter(method='filter_by_is_free')
    price = filters.RangeFilter(field_name='prices__final_price')
    is_discount = filters.BooleanFilter(method='filter_by_discount')
    level = filters.CharFilter(method='filter_by_learning_path')
    status = filters.ChoiceFilter(field_name='status', choices=Course.STATUS.choices)
    category = filters.CharFilter(method='filter_by_category')


    def filter_by_is_free(self, queryset, name, value):
        if value:
            return queryset.filter(Q(prices__final_price=0) | Q(prices__isnull=True))
        return queryset.exclude(Q(prices__final_price=0) | Q(prices__isnull=True))

    def filter_by_discount(self, queryset, name, value):
        if value:
            return queryset.filter(prices__discount_percentage__gt=0)
        return queryset.exclude(prices__discount_percentage__gt=0)

    def filter_by_learning_path(self, queryset, name, value):
        """
            Filters a queryset based on learning path levels.

            Acceptable input formats:
            
            1. "1,2"       -> Filters by start level = 1 and end level = 2.
            2. "0,3"       -> Filters by start level = 0 and end level = 3.
            3. "5,"        -> Filters by start level = 5 (end level is ignored).
            4. ",2"        -> Filters by end level = 2 (start level is ignored).
            5. "1,None"    -> Filters by start level = 1 (end level is None).
            6. ""           -> Returns original queryset (invalid input).
            7. "1,abc"     -> Returns original queryset (raises ValueError).
        """
        
        try:
            value1, value2 = value.split(',')
            value2 = None if value2 == 'None' else value2
            
            if not value1:
                return queryset.filter(learning_path__end_level__level_number=value2)
            
            if value2 == '':
                return queryset.filter(learning_path__start_level__level_number=value1)
            
            return queryset.filter(
                learning_path__start_level__level_number=value1,
                learning_path__end_level__level_number=value2
            )
        except ValueError:
            return queryset
    
    def filter_by_category(self, queryset, name, value):
        try:
            category = CourseCategory.objects.get(slug=value)
            descendants = category.get_descendants(include_self=True)
            return queryset.filter(categories__in=descendants)
        except CourseCategory.DoesNotExist:
            return queryset.none()
    
    class Meta:
        model = Course
        fields = ['order_by', 'is_free', 'price', 'is_discount', 'level', 'status', 'category']