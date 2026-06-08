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
from django.shortcuts import redirect
from django.conf import settings


class ZipPdfFileWrapper:
    """Держит zip-архив открытым, пока FileResponse дочитывает PDF."""

    def __init__(self, zip_file, pdf_stream):
        self.zip_file = zip_file
        self.pdf_stream = pdf_stream

    def read(self, *args, **kwargs):
        return self.pdf_stream.read(*args, **kwargs)

    def seekable(self):
        return False

    def close(self):
        try:
            self.pdf_stream.close()
        finally:
            self.zip_file.close()



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
            if settings.USE_SPACES:
                return redirect(book.pdf_file.url)

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
                zip_ref = zipfile.ZipFile(book.pdf_file, 'r')
                pdf_infos = [
                    info for info in zip_ref.infolist()
                    if info.filename.lower().endswith(".pdf")
                ]

                if len(pdf_infos) != 1:
                    zip_ref.close()
                    raise Http404("Archive must contain exactly one PDF")

                pdf_info = pdf_infos[0]
                pdf_stream = zip_ref.open(pdf_info, 'r')
                response = FileResponse(
                    ZipPdfFileWrapper(zip_ref, pdf_stream),
                    filename=pdf_info.filename.rsplit('/', 1)[-1],
                    content_type='application/pdf',
                )
                response['Cache-Control'] = 'public, max-age=86400'
                response['Content-Length'] = str(pdf_info.file_size)
                return response

            except zipfile.BadZipFile:
                raise Http404("Invalid zip archive")

        raise Http404
