# main/urls.py
from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
]