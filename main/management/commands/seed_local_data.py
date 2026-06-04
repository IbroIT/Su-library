from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from main.models import Book, BookTranslation, Category, CategoryTranslation


class Command(BaseCommand):
    help = "Create safe local-only demo categories and books."

    def handle(self, *args, **options):
        if not getattr(settings, "LOCAL_DEV", False):
            raise CommandError("Refusing to seed data because LOCAL_DEV is not enabled.")

        media_root = Path(settings.MEDIA_ROOT)
        demo_items = [
            {
                "category": "Тестовая медицина",
                "title": "Локальная тестовая книга: медицина",
                "author": "Demo Author",
                "description": "Тестовая книга для проверки локального каталога и ридера.",
                "year": 2025,
                "pdf": "books/pdfs/2025/10/21/upperIner.pdf",
                "cover": "books/covers/2025/01/01/book_1_cover.jpg",
            },
            {
                "category": "Тестовая библиотека",
                "title": "Локальная тестовая книга: библиотека",
                "author": "Demo Author",
                "description": "Временные данные для разработки без подключения к Heroku.",
                "year": 2025,
                "pdf": "books/pdfs/2025/10/21/книга.pdf",
                "cover": "books/covers/2025/01/01/book_2_cover.jpg",
            },
            {
                "category": "Тестовый спорт",
                "title": "Локальная тестовая книга: спорт",
                "author": "Demo Author",
                "description": "Запись создана локальной seed-командой и безопасна для тестов.",
                "year": 2025,
                "pdf": "books/pdfs/2025/10/21/книга_IKqtCFm.pdf",
                "cover": "books/covers/2025/11/04/sport-main.jpg",
            },
        ]

        created_books = 0
        created_categories = 0

        for item in demo_items:
            pdf_path = media_root / item["pdf"]
            cover_path = media_root / item["cover"]

            if not pdf_path.exists():
                self.stdout.write(self.style.WARNING(f"Skipping missing PDF: {item['pdf']}"))
                continue

            category_translation = CategoryTranslation.objects.filter(
                language="ru",
                name=item["category"],
            ).select_related("category").first()

            if category_translation:
                category = category_translation.category
            else:
                category = Category.objects.create()
                created_categories += 1
                CategoryTranslation.objects.create(
                    category=category,
                    language="ru",
                    name=item["category"],
                )

            book, book_created = Book.objects.get_or_create(
                pdf_file=item["pdf"],
                defaults={
                    "category": category,
                    "year": item["year"],
                    "cover_image": item["cover"] if cover_path.exists() else "",
                    "is_active": True,
                },
            )

            if not book_created:
                book.category = category
                book.year = item["year"]
                book.is_active = True
                if cover_path.exists():
                    book.cover_image = item["cover"]
                book.save(update_fields=["category", "year", "is_active", "cover_image", "updated_at"])
            else:
                created_books += 1

            BookTranslation.objects.update_or_create(
                book=book,
                language="ru",
                defaults={
                    "title": item["title"],
                    "author": item["author"],
                    "description": item["description"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Local demo data ready. Created categories: {created_categories}, books: {created_books}."
            )
        )
