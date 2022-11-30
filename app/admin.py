from django.contrib import admin
from .models import AppInfo, Cluster, AppDeployHistory

# Register your models here.
@admin.register(AppInfo)
class AppInfoAdmin(admin.ModelAdmin):
    pass


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    pass


@admin.register(AppDeployHistory)
class ClusterAdmin(admin.ModelAdmin):
    pass
