from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError


def validate_pdf_file_size(value):
    """Валидация размера PDF файла"""
    filesize = value.size
    if filesize > 260 * 1024 * 1024:  # 260 MB
        raise ValidationError(_('PDF файл не должен превышать 260 MB'))
    return value


def validate_image_file_size(value):
    """Валидация размера изображения"""
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10 MB
        raise ValidationError(_('Изображение не должно превышать 10 MB'))
    return value

class Category(models.Model):
    # Добавляем created_at с default значением
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))
    
    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ['created_at']
    
    def __str__(self):
        # Используем русское название по умолчанию
        russian_name = self.translations.filter(language='ru').first()
        return russian_name.name if russian_name else f"Категория {self.id}"
    
    def get_name(self, language='ru'):
        translation = self.translations.filter(language=language).first()
        return translation.name if translation else f"Категория {self.id}"

class CategoryTranslation(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('kg', 'Кыргызча'),
    ]
    
    category = models.ForeignKey(Category, related_name='translations', on_delete=models.CASCADE, verbose_name=_("Категория"))
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, verbose_name=_("Язык"))
    name = models.CharField(max_length=100, verbose_name=_("Название категории"))
    
    class Meta:
        unique_together = ('category', 'language')
        verbose_name = _("Перевод категории")
        verbose_name_plural = _("Переводы категорий")
    
    def __str__(self):
        return f"{self.name} - {self.get_language_display()}"

class Book(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Категория"))
    year = models.PositiveIntegerField(verbose_name=_("Год издания"))
    pdf_file = models.FileField(
        upload_to='books/pdfs/%Y/%m/%d/', 
        validators=[validate_pdf_file_size],
        verbose_name=_("PDF файл")
    )
    cover_image = models.ImageField(
        upload_to='books/covers/%Y/%m/%d/', 
        blank=True, 
        null=True, 
        validators=[validate_image_file_size],
        verbose_name=_("Обложка книги")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Активна"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))
    
    class Meta:
        verbose_name = _("Книга")
        verbose_name_plural = _("Книги")
        ordering = ['-created_at']
    
    def __str__(self):
        default_translation = self.translations.filter(language='ru').first()
        return default_translation.title if default_translation else f"Книга {self.id}"

class BookTranslation(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('kg', 'Кыргызча'),
    ]
    
    book = models.ForeignKey(Book, related_name='translations', on_delete=models.CASCADE, verbose_name=_("Книга"))
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, verbose_name=_("Язык"))
    title = models.CharField(max_length=200, verbose_name=_("Название книги"))
    author = models.CharField(max_length=200, verbose_name=_("Автор"))
    description = models.TextField(verbose_name=_("Описание книги"))
    
    class Meta:
        unique_together = ('book', 'language')
        verbose_name = _("Перевод книги")
        verbose_name_plural = _("Переводы книг")
    
    def __str__(self):
        return f"{self.title} - {self.get_language_display()}"