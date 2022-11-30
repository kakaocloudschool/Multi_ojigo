from django.urls import path
from .views import app_list, cluster_new

urlpatterns = [
    path("cluster_add", cluster_new, name="cluster_add"),
    path("app_add", cluster_new, name="cluster_add"),
    path("", app_list, name="app_list"),
]
