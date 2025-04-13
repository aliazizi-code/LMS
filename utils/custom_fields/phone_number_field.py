import re

from django.core.exceptions import ValidationError
from django.db import models


class PhoneNumberField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 13)
        kwargs.setdefault('unique', True)
        kwargs.setdefault('db_index', True)
        super().__init__(*args, **kwargs)

    def clean(self, value, model_instance, *args, **kwargs):
        value = super().clean(value, model_instance)
        pattern = r'^\+98[0-9]{10}$'
        if not re.match(pattern, value):
            raise ValidationError("Invalid phone number. Correct format: +98XXXXXXXXXX")
        return value
