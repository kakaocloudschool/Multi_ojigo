from django import forms
from .models import AppInfo, Cluster, AppDeployHistory


class AppInfoForm(forms.ModelForm):
    class Meta:
        model = AppInfo
        fields = [
            "app_name",
            "cluster_name",
            "auto_create_ns",
            "namespace",
            "repo_url",
            "target_revision",
            "target_path",
        ]


class ClusterForm(forms.ModelForm):
    class Meta:
        model = Cluster
        fields = ["cluster_name", "bearer_token", "kubeconfig"]

    # def __init__(self, request=None, *args, **kwargs):
    #     super(ClusterForm, self).__init__(*args, **kwargs) # 꼭 있어야 한다!
    #     self.fields['cluster_name'].label = '클러스터 이름'
    #     self.fields['bearer_token'].label = '토큰 값 입력'
    #     self.fields['kubeconfig'].label = 'config 파일 업로드'


class DeployForm(forms.ModelForm):
    class Meta:
        model = AppDeployHistory
        fields = [
            "deploy_type",
        ]
