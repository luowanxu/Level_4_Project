# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('search-city/', views.search_city, name='search_city'),
    path('city-places/', views.get_city_places, name='city_places'),
]