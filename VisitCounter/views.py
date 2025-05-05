from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache


class ContentVisitView(APIView):
    def post(self, request, model_name, object_slug):
        
        session_key = request.session.session_key or request.session.create().session_key
        cache_visitor_unique_key = f"content_unique_visit:{model_name}:{object_slug}:{session_key}"
        cache_visitor_key = f"content_visit:{model_name}:{object_slug}"
        
        if not cache.get(cache_visitor_unique_key):
            cache.set(cache_visitor_unique_key, {
                "model_name": model_name.lower(),
                "object_slug": object_slug,
                "session_key": session_key
            }, timeout=2*3600)
        
        if not cache.get(cache_visitor_key):
            cache.set(cache_visitor_key, 1, timeout=2*3600)
        else:
            cache.incr(cache_visitor_key, 1)
            
            
        return Response({}, status=status.HTTP_200_OK)
        
        