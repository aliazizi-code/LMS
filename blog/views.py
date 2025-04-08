from rest_framework import generics
from .serializers import ArticleCategorySerializer
from .models import *


class CategoryListView(generics.ListAPIView):
    serializer_class = ArticleCategorySerializer
    queryset = ArticleCategory.objects.filter(parent=None, is_active=True)







