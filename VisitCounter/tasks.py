from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db.models import F, Case, When, Q

from .models import ContentVisit


@shared_task
def save_content_visits_to_db():
    keys_unique_view = cache.keys("content_unique_visit:*")
    keys_view = cache.keys("content_visit:*")
    if not keys_unique_view and keys_view:
        return
    
    views_to_create = []
    unique_views_to_create = {}
    objects_to_update_dict = {}
    content_type_cache = {}
    unique_visit_keys = []
    
    # region unique view
    
    for key in keys_unique_view:
        data = cache.get(key)
        if not data:
            continue

        model_name = data.get('model_name')
        object_slug = data.get('object_slug')
        session_key = data.get('session_key')
        if not model_name or not object_slug or not session_key:
            continue

        unique_visit_keys.append((model_name, object_slug, session_key))
    
    unique_visit_keys = list(set(unique_visit_keys))
    
    query = Q()
    for model_name, object_slug, session_key in unique_visit_keys:
        query |= Q(content_type__model=model_name, object_slug=object_slug, session_key=session_key)
    
    existing_visits = set()
    if query:
        for visit in ContentVisit.objects.filter(query).values(
            'content_type__model', 'object_slug', 'session_key'
        ):
            key_tuple = (visit['content_type__model'], visit['object_slug'], visit['session_key'])
            existing_visits.add(key_tuple)

    for model_name, object_slug, session_key in unique_visit_keys:
        try:
            if model_name in content_type_cache:
                content_type = content_type_cache[model_name]
            else:
                content_type = ContentType.objects.get(model=model_name)
                content_type_cache[model_name] = content_type

            model_class = content_type.model_class()
            content = model_class.objects.get(
                slug=object_slug,
                is_deleted=False,
                is_published=True,
            )
        except (ObjectDoesNotExist, ContentType.DoesNotExist):
            continue

        if (model_name, object_slug, session_key) not in existing_visits:
            views_to_create.append(ContentVisit(
                content_type=content_type,
                object_slug=object_slug,
                session_key=session_key,
            ))
            objects_to_update_dict[(model_name, object_slug)] = content

    if views_to_create:
        ContentVisit.objects.bulk_create(views_to_create, ignore_conflicts=True)

        objects_to_update = list(objects_to_update_dict.values())

        model_class.objects.filter(
            slug__in=[obj.slug for obj in objects_to_update],
            is_deleted=False,
            is_published=True
        ).update(count_unique_views=F('count_unique_views') + 1)

    
    # endregion
    
    # region view
    
    for key in keys_view:
        cached_data = cache.get(key)
        if not cached_data:
            continue
        
        parts = key.split(':')
        if len(parts) < 3:
            continue
        
        data = key.split(':')
        
        model_name = parts[1]
        object_slug = parts[2]
        if not model_name or not object_slug:
            continue
        
        key_view = f"content_visit:{model_name}:{object_slug}"
        visit_count = cache.get(key_view)
        if not visit_count:
            continue
        
        key_tuple = (model_name, object_slug)
        unique_views_to_create[key_tuple] = unique_views_to_create.get(key_tuple, 0) + int(visit_count)
        
    groups = {}
    for (model_name, slug), total_increment in unique_views_to_create.items():
        groups.setdefault(model_name, {})[slug] = total_increment
    
    for model_name, slug_dict in groups.items():
        try:
            content_type = ContentType.objects.get(model=model_name)
        except ContentType.DoesNotExist:
            continue

        model_class = content_type.model_class()

        cases = []
        for slug, increment in slug_dict.items():
            cases.append(When(slug=slug, then=F('count_views') + increment))

        model_class.objects.filter(
            slug__in=list(slug_dict.keys()),
            is_deleted=False,
            is_published=True,
        ).update(
            count_views=Case(
                *cases,
                default=F('count_views'),
                output_field=model_class._meta.get_field('count_views').__class__()
            )
        )
    
    # endregion
    
    if keys_view:
        cache.delete_many(keys_view)
    if keys_unique_view:
        cache.delete_many(keys_unique_view)
