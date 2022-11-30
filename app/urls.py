from django.urls import path
from .views import app_list

urlpatterns = [
    path("", app_list, name="app_list"),
]
