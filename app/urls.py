from django.urls import path
from .views import (
    new_cluster,
    new_app,
    app_list,
    cluster_list,
    deploy_app,
    history_app,
    delete_app,
    test_web,
    bluegreen,
    rollingupdate,
)

urlpatterns = [
    path("new_cluster", new_cluster, name="new_cluster"),
    path("new_app", new_app, name="new_app"),
    path("", app_list, name="app_list"),
    path("cluster_list", cluster_list, name="cluster_list"),
    path("delete_app/<str:pk>", delete_app, name="delete_app"),
    path("appinfo_deploy/<str:pk>", deploy_app, name="appinfo_deploy"),
    path("appinfo_deploy/<str:pk>/bluegreen", bluegreen, name="bluegreen"),
    path("appinfo_deploy/<str:pk>/rollingupdate", rollingupdate, name="rollingupdate"),
    path("appinfo_history/<str:q>", history_app, name="appinfo_history"),
    # path("test_web", test_web, name="test_web"),
]
