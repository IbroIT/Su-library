# main/views.py
import zipfile

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, pagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Category
from .serializers import BookDetailSerializer, BookListSerializer, CategorySerializer


class ZipPdfFileWrapper:
    """Keeps the zip archive open while FileResponse streams the inner PDF."""

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

    def get_queryset(self):  # type: ignore
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
                'request': request,
            }
        )
        return Response(serializer.data)


class BookDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = BookDetailSerializer

    def get_queryset(self):  # type: ignore
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

    def get_queryset(self):  # type: ignore
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

    def _parse_range_header(self, range_header, file_size):
        if not range_header or not range_header.startswith('bytes='):
            return None

        range_value = range_header.removeprefix('bytes=').strip()
        if ',' in range_value:
            return None

        start_value, separator, end_value = range_value.partition('-')
        if separator != '-':
            return None

        try:
            if start_value == '':
                suffix_length = int(end_value)
                if suffix_length <= 0:
                    return None
                start = max(file_size - suffix_length, 0)
                end = file_size - 1
            else:
                start = int(start_value)
                end = int(end_value) if end_value else file_size - 1
        except ValueError:
            return None

        if start < 0 or end < start or start >= file_size:
            return None

        return start, min(end, file_size - 1)

    def _pdf_range_response(self, pdf_file, file_name, request):
        file_size = pdf_file.size
        range_result = self._parse_range_header(request.headers.get('Range'), file_size)

        if range_result is None:
            pdf_file.open('rb')
            response = FileResponse(
                pdf_file,
                filename=file_name,
                content_type='application/pdf',
            )
            response['Content-Length'] = str(file_size)
            response['Cache-Control'] = 'public, max-age=86400'
            response['Accept-Ranges'] = 'bytes'
            return response

        start, end = range_result
        length = end - start + 1

        pdf_file.open('rb')
        try:
            pdf_file.seek(start)
            data = pdf_file.read(length)
        finally:
            pdf_file.close()

        response = HttpResponse(data, status=206, content_type='application/pdf')
        response['Content-Length'] = str(len(data))
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'public, max-age=86400'
        response['Content-Disposition'] = f'inline; filename="{file_name}"'
        return response

    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk, is_active=True)
        except Book.DoesNotExist:
            raise Http404

        if not book.pdf_file:
            raise Http404

        file_name = book.pdf_file.name.lower()

        if file_name.endswith(".pdf"):
            if settings.USE_SPACES:
                return redirect(book.pdf_file.url)

            return self._pdf_range_response(
                book.pdf_file,
                book.pdf_file.name.rsplit('/', 1)[-1],
                request,
            )

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
