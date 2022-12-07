from django.db import models


class Cluster(models.Model):
    cluster_name = models.CharField(
        max_length=100, primary_key=True, verbose_name="클러스터 이름"
    )
    cluster_type = models.CharField(max_length=20)
    kubeconfig = models.FileField(null=True, upload_to="", verbose_name="kubeconfig 파일")
    cluster_url = models.TextField()
    user_id = models.CharField(max_length=100)
    insert_date = models.DateTimeField(auto_now_add=True)
    bearer_token = models.TextField(verbose_name="쿠버네티스 계정 토큰")

    def __str__(self):
        return self.cluster_name


# Create your models here.
class AppInfo(models.Model):
    app_name = models.CharField(max_length=100, primary_key=True, verbose_name="APP 이름")
    cluster_name = models.ForeignKey(
        Cluster, on_delete=models.CASCADE, verbose_name="클러스터 이름"
    )
    auto_create_ns = models.BooleanField(default=False, verbose_name="네임스페이스 생성")
    namespace = models.CharField(max_length=100, verbose_name="네임스페이스")
    repo_url = models.CharField(max_length=200, verbose_name="레파지토리 주소")
    target_revision = models.CharField(max_length=100, verbose_name="타겟 브랜치")
    target_path = models.CharField(max_length=100, verbose_name="레파지토리 경로")
    insert_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
    update_user = models.CharField(max_length=100)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.app_name


class Scheduler(models.Model):
    MY_CHOICES = (  # 각 튜플의 첫 번째 요소는 DB에 저장할 실제 값이고, 두 번째 요소는 display 용 이름이다.
        ("RollingUpdate", "롤링 업데이트 배포"),
        ("BlueGreen", "블루그린 배포"),
        ("Canary", "카나리 배포"),
    )
    app_name = models.ForeignKey(AppInfo, on_delete=models.RESTRICT)
    deploy_type = models.CharField(
        max_length=20, choices=MY_CHOICES, default="RollingUpdate"
    )
    cluster_name = models.CharField(max_length=100)
    cluster_url = models.TextField()
    cluster_token = models.TextField()
    namespace = models.CharField(max_length=100)
    deployment = models.CharField(max_length=100)
    container = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    before_color = models.CharField(max_length=10, null=True)
    change_color = models.CharField(max_length=10, null=True)
    target_service = models.CharField(max_length=100, null=True)
    step = models.CharField(max_length=30)
    insert_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
    update_user = models.CharField(max_length=100)
    update_at = models.DateTimeField(auto_now=True)
    schedule_dt = models.DateTimeField()
    manager_user = models.CharField(max_length=100)


class CanaryStategyMaster(models.Model):
    sterategy = models.CharField(max_length=100)
    step = models.CharField(max_length=10)
    Percentage = models.CharField(max_length=3)
    timewait = models.IntegerField()


class CananryDeployHistory(models.Model):
    appdeployrevision_id = models.IntegerField()
    sterategy = models.CharField(max_length=100)
    step = models.CharField(max_length=10)
    Percentage = models.CharField(max_length=3)
    timewait = models.IntegerField()
    real_percentage = models.CharField(max_length=3, null=True)
    pre_replicaset = models.IntegerField(null=True)
    new_replicaset = models.IntegerField(null=True)
    auto_deploy_time = models.DateTimeField(null=True)
    complete_yn = models.CharField(max_length=1, null=True)


class AppDeployRevision(models.Model):
    app_name = models.CharField(max_length=100)
    deploy_type = models.CharField(max_length=20)
    cluster_name = models.CharField(max_length=100)
    cluster_url = models.TextField()
    cluster_token = models.TextField()
    namespace = models.CharField(max_length=100)
    deployment = models.CharField(max_length=100)
    new_deployment = models.CharField(max_length=100, null=True)
    container = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    before_color = models.CharField(max_length=10, null=True)
    change_color = models.CharField(max_length=10, null=True)
    target_service = models.CharField(max_length=100, null=True)
    before_replicas = models.CharField(max_length=10, null=True)
    step = models.CharField(max_length=30)
    canary_sterategy = models.CharField(max_length=100, null=True)
    insert_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
    update_user = models.CharField(max_length=100)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.app_name


class AppDeployHistory(models.Model):
    MY_CHOICES = (  # 각 튜플의 첫 번째 요소는 DB에 저장할 실제 값이고, 두 번째 요소는 display 용 이름이다.
        ("ROLLINGUPDATE", "롤링 업데이트 배포"),
        ("BLUEGREEN", "블루그린 배포"),
        ("CANARY", "카나리 배포"),
    )
    AppDeployRevision_id = models.CharField(max_length=100)
    app_name = models.CharField(max_length=100, verbose_name="APP 이름")
    deploy_type = models.CharField(
        max_length=20, choices=MY_CHOICES, default="RollingUpdate"
    )
    cluster_name = models.CharField(max_length=100)
    cluster_url = models.TextField()
    cluster_token = models.TextField()
    namespace = models.CharField(max_length=100)
    deployment = models.CharField(max_length=100)
    new_deployment = models.CharField(max_length=100, null=True)
    container = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    before_color = models.CharField(max_length=10, null=True)
    change_color = models.CharField(max_length=10, null=True)
    target_service = models.CharField(max_length=100, null=True)
    before_replicas = models.CharField(max_length=10, null=True)
    step = models.CharField(max_length=30)
    manager_user = models.CharField(max_length=100)
    canary_sterategy = models.CharField(max_length=100, null=True)
    insert_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
