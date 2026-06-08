import shutil
import tempfile
import zipfile
from io import BytesIO

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

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
    STORAGES=TEST_STORAGES,
)
class BookApiTests(APITestCase):
    def setUp(self):
        self.temp_media_dir = tempfile.mkdtemp(prefix='library-tests-')
        self.override = override_settings(MEDIA_ROOT=self.temp_media_dir)
        self.override.enable()

        category = Category.objects.create()
        CategoryTranslation.objects.create(
            category=category,
            language='ru',
            name='Тестовая категория',
        )

        pdf_file = SimpleUploadedFile(
            'sample.pdf',
            b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            content_type='application/pdf',
        )

        self.book = Book.objects.create(
            category=category,
            year=2026,
            pdf_file=pdf_file,
            is_active=True,
        )
        BookTranslation.objects.create(
            book=self.book,
            language='ru',
            title='Тестовая книга',
            author='Тестовый автор',
            description='Описание книги для теста.',
        )

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_media_dir, ignore_errors=True)

    def test_book_detail_returns_pdf_file_url(self):
        response = self.client.get(f'/api/books/{self.book.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.book.pk)
        self.assertIn('pdf_file_url', response.data)
        self.assertTrue(response.data['pdf_file_url'].endswith('.pdf'))

    def test_book_file_endpoint_returns_pdf_stream(self):
        response = self.client.get(f'/api/book-file/{self.book.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('Cache-Control', response)

    def test_book_list_returns_pdf_file_url(self):
        response = self.client.get('/api/books/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('pdf_file_url', response.data[0])
        self.assertTrue(response.data[0]['pdf_file_url'].endswith('.pdf'))

    def test_zip_book_uses_book_file_endpoint(self):
        category = Category.objects.create()
        CategoryTranslation.objects.create(
            category=category,
            language='ru',
            name='ZIP категория',
        )

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                'inside.pdf',
                b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF',
            )
        zip_buffer.seek(0)

        zip_book = Book.objects.create(
            category=category,
            year=2026,
            pdf_file=SimpleUploadedFile(
                'sample.zip',
                zip_buffer.read(),
                content_type='application/zip',
            ),
            is_active=True,
        )
        BookTranslation.objects.create(
            book=zip_book,
            language='ru',
            title='ZIP книга',
            author='Автор ZIP',
            description='Описание ZIP книги.',
        )

        detail_response = self.client.get(f'/api/books/{zip_book.pk}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIn(f'/api/book-file/{zip_book.pk}/', detail_response.data['pdf_file_url'])

        file_response = self.client.get(f'/api/book-file/{zip_book.pk}/')
        self.assertEqual(file_response.status_code, status.HTTP_200_OK)
        self.assertEqual(file_response['Content-Type'], 'application/pdf')
        self.assertEqual(file_response['Content-Length'], str(len(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF')))
