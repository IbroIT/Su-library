from pathlib import Path

from django.conf import settings
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Book, BookTranslation, Category, CategoryTranslation


TEST_STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}


@override_settings(
    USE_SPACES=False,
    MEDIA_URL='/media/',
    MEDIA_ROOT=Path(settings.BASE_DIR) / 'media',
    STORAGES=TEST_STORAGES,
)
class BookApiTests(APITestCase):
    def setUp(self):
        category = Category.objects.create()
        CategoryTranslation.objects.create(
            category=category,
            language='ru',
            name='Тестовая категория',
        )

        self.book = Book.objects.create(
            category=category,
            year=2026,
            pdf_file='books/pdfs/2025/10/21/upperIner.pdf',
            is_active=True,
        )
        BookTranslation.objects.create(
            book=self.book,
            language='ru',
            title='Тестовая книга',
            author='Тестовый автор',
            description='Описание книги для теста.',
        )

    def test_book_detail_returns_pdf_file_url(self):
        response = self.client.get(f'/api/books/{self.book.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.book.pk)
        self.assertIn('pdf_file_url', response.data)
        self.assertIn(f'/api/book-file/{self.book.pk}/', response.data['pdf_file_url'])

    def test_book_file_endpoint_returns_pdf_stream(self):
        response = self.client.get(f'/api/book-file/{self.book.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('Cache-Control', response)

    def test_book_file_endpoint_supports_range_requests(self):
        response = self.client.get(
            f'/api/book-file/{self.book.pk}/',
            HTTP_RANGE='bytes=0-9',
        )

        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        self.assertEqual(response['Content-Length'], '10')
        self.assertTrue(response['Content-Range'].startswith('bytes 0-9/'))
        self.assertEqual(len(response.content), 10)
        self.assertTrue(response.content.startswith(b'%PDF'))
