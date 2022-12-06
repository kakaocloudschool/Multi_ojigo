from django.urls import path
from .views import (
    new_cluster,
    new_app,
    app_list,
    cluster_list,
    deploy_app,
    delete_app,
    bluegreen,
    rollingupdate,
    bluegreen_detail,
    canary,
    canary_detail,
    new_schedule,
    scheduler,
    app_deploy_history,
    app_deploy_history_all,
    schedule_list,
)

urlpatterns = [
    path("new_cluster", new_cluster, name="new_cluster"),
    path("new_app", new_app, name="new_app"),
    path("", app_list, name="app_list"),
    path("cluster_list", cluster_list, name="cluster_list"),
    path("delete_app/<str:pk>", delete_app, name="delete_app"),
    path("appinfo_deploy/<str:pk>", deploy_app, name="appinfo_deploy"),
    path("appinfo_deploy/<str:pk>/bluegreen", bluegreen, name="bluegreen"),
    path(
        "appinfo_deploy/<str:app_name>/bluegreen/<int:pk>",
        bluegreen_detail,
        name="bluegreen_detail",
    ),
    path("appinfo_deploy/<str:pk>/canary", canary, name="canary"),
    path(
        "appinfo_deploy/<str:app_name>/canary/<int:pk>",
        canary_detail,
        name="canary_detail",
    ),
    path("appinfo_deploy/<str:pk>/rollingupdate", rollingupdate, name="rollingupdate"),
    path("app_deploy_history", app_deploy_history_all, name="app_deploy_history_all"),
    path(
        "app_deploy_history/<str:app_name>",
        app_deploy_history,
        name="app_deploy_history",
    ),
    # path("test_web", test_web, name="test_web"),

    path("schedule_list/<str:pk>", schedule_list, name="schedule_list"),
    path("new_schedule/<str:pk>", new_schedule, name="new_schedule"),
    path("scheduler", scheduler, name="scheduler"),
]
