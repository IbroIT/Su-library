# main/views.py
from rest_framework import generics
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book, Category
from .serializers import BookSerializer, CategorySerializer

class BookListView(generics.ListAPIView):
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'year']
    
    def get_queryset(self):
        return Book.objects.filter(is_active=True).select_related('category').prefetch_related('translations')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        language = request.GET.get('language', 'ru')
        
        serializer = self.get_serializer(
            queryset, 
            many=True,
            context={
                'language': language,
                'request': request  # Важно: передаем request
            }
        )
        return Response(serializer.data)

class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.prefetch_related('translations')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        language = request.GET.get('language', 'ru')
        
        serializer = self.get_serializer(
            queryset, 
            many=True,
            context={'language': language}
        )
        return Response(serializer.data)