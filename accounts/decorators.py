from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from functools import wraps

def debug_sensitive_ratelimit(**ratelimit_args):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not settings.DEBUG:  # فقط زمانی که DEBUG=False باشد
                return ratelimit(**ratelimit_args)(view_func)(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
