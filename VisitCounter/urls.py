from django.urls import re_path
from .views import ContentVisitView

urlpatterns = [
    re_path(
        r'^track-view/(?P<model_name>[\w\-]+)/(?P<object_slug>[\w\-آ-ی]+)/?$',
        ContentVisitView.as_view(),
        name='track-view'
    ),
]
