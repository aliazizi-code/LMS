from rest_framework import generics
from .serializers import ArticleCategorySerializer, ArticleSerializer
from .models import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated


class CategoryListView(generics.ListAPIView):
    serializer_class = ArticleCategorySerializer
    queryset = ArticleCategory.objects.filter(parent=None, is_active=True)


class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    





