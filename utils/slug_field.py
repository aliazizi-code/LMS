import re
from django.db import models

def slugify(value):
    cleaned_value = re.sub(r'[^\w\s-]', '', str(value))
    return re.sub(r'[-\s]+', '-', cleaned_value).lower().strip('-')

class AutoSlugField(models.SlugField):
    def __init__(self, source_field=None, *args, **kwargs):
        self.source_field = source_field
        kwargs.setdefault('max_length', 255)
        kwargs.setdefault('unique', True)
        kwargs.setdefault('db_index', True)
        kwargs.setdefault('editable', False)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if self.source_field:
            value = getattr(model_instance, self.source_field, None)
            if value:
                slug = slugify(value)
                setattr(model_instance, self.attname, slug)
        return super().pre_save(model_instance, add)