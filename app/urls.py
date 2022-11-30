from django.urls import path
from .views import new_cluster, new_app, app_list

urlpatterns = [
    path("new_cluster", new_cluster, name="new_cluster"),
    path("new_app", new_app, name="new_app"),
    path("", app_list, name="app_list"),
]
