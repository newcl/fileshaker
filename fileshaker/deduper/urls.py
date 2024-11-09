from django.urls import path
from .views import scan_directory_view

urlpatterns = [
    path('scan/', scan_directory_view, name='scan_directory'),
]
