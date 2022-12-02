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
        Cluster, on_delete=models.RESTRICT, verbose_name="클러스터 이름"
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




class AppDeployHistory(models.Model):
    MY_CHOICES = (  # 각 튜플의 첫 번째 요소는 DB에 저장할 실제 값이고, 두 번째 요소는 display 용 이름이다.
        ("RollingUpdate", "롤링 업데이트 배포"),
        ("BlueGreen", "블루그린 배포"),
        ("Canary", "카나리 배포"),
    )

    app_name = models.ForeignKey(AppInfo, on_delete=models.RESTRICT)
    revision = models.CharField(max_length=100)
    deploy_type = models.CharField(max_length=20, choices=MY_CHOICES, default="RollingUpdate")
    user = models.CharField(max_length=100)
    manager_user = models.CharField(max_length=100)
    insert_at = models.DateTimeField(auto_now_add=True)
