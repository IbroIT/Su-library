from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Category, CategoryTranslation, Book, BookTranslation

class CategoryTranslationInline(admin.StackedInline):
    model = CategoryTranslation
    extra = 3
    max_num = 3  # Ограничиваем тремя языками
    min_num = 3  # Требуем все три языка
    verbose_name = _("Перевод")
    verbose_name_plural = _("Переводы категории")
    fields = ['language', 'name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_russian_name', 'get_english_name', 'get_kyrgyz_name', 'created_at']
    search_fields = ['translations__name']
    list_filter = ['created_at']
    inlines = [CategoryTranslationInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        (_("Информация"), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_russian_name(self, obj):
        translation = obj.translations.filter(language='ru').first()
        return translation.name if translation else "—"
    get_russian_name.short_description = _("Название (рус)")
    get_russian_name.admin_order_field = 'translations__name'
    
    def get_english_name(self, obj):
        translation = obj.translations.filter(language='en').first()
        return translation.name if translation else "—"
    get_english_name.short_description = _("Название (англ)")
    
    def get_kyrgyz_name(self, obj):
        translation = obj.translations.filter(language='ky').first()
        return translation.name if translation else "—"
    get_kyrgyz_name.short_description = _("Название (кырг)")
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Проверяем, что все три языка добавлены
        translations_count = obj.translations.count()
        if translations_count < 3:
            self.message_user(
                request, 
                f"Внимание: добавлено только {translations_count} переводов из 3 необходимых", 
                level='WARNING'
            )

class BookTranslationInline(admin.StackedInline):
    model = BookTranslation
    extra = 3
    max_num = 3  # Ограничиваем тремя языками
    min_num = 3  # Требуем все три языка
    verbose_name = _("Перевод")
    verbose_name_plural = _("Переводы книги")
    fieldsets = [
        (None, {
            'fields': ['language', 'title', 'author', 'description'],
            'classes': ['wide']
        })
    ]

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'get_russian_title', 
        'get_russian_author', 
        'get_category_russian_name',
        'year', 
        'is_active',
        'created_at'
    ]
    list_filter = ['category', 'year', 'is_active', 'created_at']
    search_fields = [
        'translations__title', 
        'translations__author',
        'category__translations__name'
    ]
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BookTranslationInline]
    fieldsets = [
        (_("Основная информация"), {
            'fields': ['category', 'year', 'pdf_file', 'is_active']
        }),
        (_("Даты"), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_russian_title(self, obj):
        translation = obj.translations.filter(language='ru').first()
        return translation.title if translation else "—"
    get_russian_title.short_description = _("Название (рус)")
    get_russian_title.admin_order_field = 'translations__title'
    
    def get_russian_author(self, obj):
        translation = obj.translations.filter(language='ru').first()
        return translation.author if translation else "—"
    get_russian_author.short_description = _("Автор (рус)")
    
    def get_category_russian_name(self, obj):
        return obj.category.get_name('ru')
    get_category_russian_name.short_description = _("Категория")
    get_category_russian_name.admin_order_field = 'category__translations__name'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Проверяем, что все три языка добавлены
        translations_count = obj.translations.count()
        if translations_count < 3:
            self.message_user(
                request, 
                f"Внимание: добавлено только {translations_count} переводов из 3 необходимых", 
                level='WARNING'
            )

# Админки только для просмотра переводов
@admin.register(BookTranslation)
class BookTranslationAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'book', 'author']
    list_filter = ['language', 'book__category']
    search_fields = ['title', 'author', 'description']
    readonly_fields = ['book']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(CategoryTranslation)
class CategoryTranslationAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'category']
    list_filter = ['language', 'category']
    search_fields = ['name']
    readonly_fields = ['category']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False