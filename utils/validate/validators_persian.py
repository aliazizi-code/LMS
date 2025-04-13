import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_persian(value):
    if not re.match(r'^[\u0600-\u06FF\s]+$', value):
        raise ValidationError(_('فقط کاراکترهای فارسی مجاز است.'))
