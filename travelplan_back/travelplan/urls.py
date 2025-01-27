# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('search-city/', views.search_city, name='search_city'),
    path('city-places/', views.get_city_places, name='city_places'),
    path('cluster-places/', views.cluster_places, name='cluster_places'),
    path('update-schedule/', views.update_schedule, name='update_schedule'),
    path('export-calendar/', views.export_calendar, name='export_calendar'),
]