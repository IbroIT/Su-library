# main/urls.py
from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('book-file/<int:pk>/', views.BookOnlyListAPIView.as_view(), name='book-file')
]
