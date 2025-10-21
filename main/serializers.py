# main/serializers.py
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
        translation = obj.translations.filter(language=language).first()
        return translation.name if translation else f"Категория {obj.id}"

class BookTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookTranslation
        fields = ['language', 'title', 'author', 'description']

class BookSerializer(serializers.ModelSerializer):
    translations = BookTranslationSerializer(many=True, read_only=True)
    title = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'category', 'category_name', 
            'year', 'pdf_file', 'pdf_url', 'title', 'author', 'description',
            'is_active', 'created_at', 'translations'
        ]
    
    def get_title(self, obj):
        language = self.context.get('language', 'ru')
        translation = obj.translations.filter(language=language).first()
        return translation.title if translation else f"Книга {obj.id}"
    
    def get_author(self, obj):
        language = self.context.get('language', 'ru')
        translation = obj.translations.filter(language=language).first()
        return translation.author if translation else "Неизвестный автор"
    
    def get_description(self, obj):
        language = self.context.get('language', 'ru')
        translation = obj.translations.filter(language=language).first()
        return translation.description if translation else ""
    
    def get_category_name(self, obj):
        language = self.context.get('language', 'ru')
        translation = obj.category.translations.filter(language=language).first()
        return translation.name if translation else "Категория"
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                # Правильное формирование URL
                return request.build_absolute_uri(obj.pdf_file.url)
            else:
                # Fallback - убедитесь что нет лишних префиксов
                return f"http://localhost:8000{obj.pdf_file.url}"
        return None
