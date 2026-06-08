from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from .models import Book, BookTranslation, Category, CategoryTranslation


class CategoryTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryTranslation
        fields = ['language', 'name']


class CategorySerializer(serializers.ModelSerializer):
    translations = CategoryTranslationSerializer(many=True, read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'translations']

    def get_name(self, obj):
        language = self.context.get('language', 'ru')
        for translation in obj.translations.all():
            if translation.language == language:
                return translation.name
        return f"Категория {obj.id}"


class BookTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTranslation
        fields = ['language', 'title', 'author', 'description']


class BookBaseSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()

    def _get_translation(self, obj):
        language = self.context.get('language', 'ru')
        for translation in obj.translations.all():
            if translation.language == language:
                return translation
        return None

    def _build_absolute_url(self, file_field):
        if not file_field:
            return None

        request = self.context.get('request')
        url = file_field.url
        return request.build_absolute_uri(url) if request else f"http://localhost:8000{url}"

    def _build_book_file_endpoint_url(self, obj):
        request = self.context.get('request')
        url = reverse('main:book-file', args=[obj.pk])
        return request.build_absolute_uri(url) if request else f"http://localhost:8000{url}"

    def _build_book_reader_url(self, obj):
        if not obj.pdf_file:
            return None

        file_name = obj.pdf_file.name.lower()
        if not getattr(settings, 'USE_SPACES', False) or file_name.endswith('.zip'):
            return self._build_book_file_endpoint_url(obj)

        return self._build_absolute_url(obj.pdf_file)

    def get_title(self, obj):
        translation = self._get_translation(obj)
        return translation.title if translation else f"Книга {obj.id}"

    def get_author(self, obj):
        translation = self._get_translation(obj)
        return translation.author if translation else "Неизвестный автор"

    def get_description(self, obj):
        translation = self._get_translation(obj)
        return translation.description if translation else ""

    def get_category_name(self, obj):
        language = self.context.get('language', 'ru')
        for translation in obj.category.translations.all():
            if translation.language == language:
                return translation.name
        return "Категория"

    def get_cover_image_url(self, obj):
        return self._build_absolute_url(obj.cover_image)


class BookListSerializer(BookBaseSerializer):
    class Meta:
        model = Book
        fields = [
            'id', 'category', 'category_name',
            'year', 'cover_image', 'cover_image_url',
            'title', 'author', 'description',
            'is_active', 'created_at',
        ]


class BookDetailSerializer(BookBaseSerializer):
    translations = BookTranslationSerializer(many=True, read_only=True)
    pdf_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'category', 'category_name',
            'year', 'cover_image', 'cover_image_url',
            'pdf_file', 'pdf_file_url',
            'title', 'author', 'description',
            'is_active', 'created_at', 'translations',
        ]

    def get_pdf_file_url(self, obj):
        return self._build_book_reader_url(obj)


BookSerializer = BookListSerializer
