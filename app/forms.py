from django import forms
from .models import AppInfo, Cluster


class AppInfoForm(forms.ModelForm):
    class Meta:
        model = AppInfo
        fields = "__all__"


class ClusterForm(forms.ModelForm):
    class Meta:
        model = Cluster
        fields = ["cluster_name", "bearer_token", "kubeconfig"]
