from django.db import models


class Cluster(models.Model):
    cluster_name = models.CharField(max_length=100, primary_key=True)
    cluster_type = models.CharField(max_length=20)
    kubeconfig = models.FileField(null=True, upload_to="")
    cluster_url = models.TextField()
    user_id = models.CharField(max_length=100)
    insert_date = models.DateTimeField(auto_now_add=True)
    bearer_token = models.TextField()


# Create your models here.
class AppInfo(models.Model):
    app_name = models.CharField(max_length=100, primary_key=True)
    cluster_name = models.ForeignKey(Cluster, on_delete=models.RESTRICT)
    namespace = models.CharField(max_length=100)
    repo_url = models.TextField()
    target_revision = models.TextField()
    target_path = models.TextField()
    insert_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
    update_user = models.CharField(max_length=100)
    update_at = models.DateTimeField(auto_now=True)


class AppDeployHistory(models.Model):
    app_name = models.ForeignKey(AppInfo, on_delete=models.RESTRICT)
    revision = models.CharField(max_length=100)
    deploy_type = models.CharField(max_length=5)
    user = models.CharField(max_length=100)
    manager_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
