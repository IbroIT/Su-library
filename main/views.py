# main/views.py
import zipfile
from io import BytesIO

from rest_framework import generics, pagination
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book, Category
from .serializers import BookDetailSerializer, BookListSerializer, CategorySerializer
from django.http import Http404, FileResponse



class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 1000


class BookListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = BookListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'year']
        
    def get_queryset(self): # type: ignore
        return Book.objects.filter(is_active=True).select_related('category').prefetch_related(
            'translations',
            'category__translations',
        )
    
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


class BookDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = BookDetailSerializer

    def get_queryset(self): # type: ignore
        return Book.objects.filter(is_active=True).select_related('category').prefetch_related(
            'translations',
            'category__translations',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.GET.get('language', 'ru')
        return context

class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    
    def get_queryset(self): # type: ignore
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



class BookOnlyListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk, is_active=True)
        except Book.DoesNotExist:
            raise Http404

        if not book.pdf_file:
            raise Http404

        file_name = book.pdf_file.name.lower()

        # Если это обычный PDF — отдаём напрямую
        if file_name.endswith(".pdf"):
            book.pdf_file.open('rb')
            response = FileResponse(
                book.pdf_file,
                filename=book.pdf_file.name.rsplit('/', 1)[-1],
                content_type='application/pdf',
            )
            response['Cache-Control'] = 'public, max-age=86400'
            response['Accept-Ranges'] = 'bytes'
            return response

        # Если это ZIP — извлекаем PDF в памяти
        if file_name.endswith(".zip"):
            try:
                book.pdf_file.open('rb')
                with zipfile.ZipFile(BytesIO(book.pdf_file.read()), 'r') as zip_ref:
                    pdf_files = [f for f in zip_ref.namelist() if f.lower().endswith(".pdf")]

                    if len(pdf_files) != 1:
                        raise Http404("Archive must contain exactly one PDF")

                    pdf_name = pdf_files[0]
                    pdf_data = zip_ref.read(pdf_name)  # читаем PDF в память
                    pdf_file_like = BytesIO(pdf_data)

                    response = FileResponse(
                        pdf_file_like,
                        filename=pdf_name.rsplit('/', 1)[-1],
                        content_type='application/pdf',
                    )
                    response['Cache-Control'] = 'public, max-age=86400'
                    response['Accept-Ranges'] = 'bytes'
                    return response

            except zipfile.BadZipFile:
                raise Http404("Invalid zip archive")

        raise Http404
