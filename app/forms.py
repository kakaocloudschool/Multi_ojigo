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


class DeployForm(forms.ModelForm):
    class Meta:
        model = AppDeployHistory
        fields = [
            "deploy_type",
        ]
        widgets = {
            #'deploy_type': forms.RadioSelect,
            'deploy_type': forms.Select,
        }
