from django import forms
from .models import AppInfo, Cluster, AppDeployHistory, AppDeployRevision, Scheduler

class DeployMethodForm(forms.Form):
    cluster_url = forms.CharField(max_length=100)
    cluster_token = forms.Textarea()
    app_name = forms.CharField(label="AppName", max_length=100)
    namespace = forms.CharField(label="namespace", max_length=100)
    deployment = forms.CharField(label="deployment", max_length=100)
    service = forms.CharField(label="service", max_length=100)
    container = forms.CharField(label="container", max_length=100)
    tag = forms.CharField(label="tag", max_length=20)
    type = forms.CharField(max_length=10)
    replicaset = forms.IntegerField(initial=0)


class AppDeployRevisionForm(forms.ModelForm):
    class Meta:
        model = AppDeployRevision
        fields = "__all__"

class SchedulerForm(forms.ModelForm):
    class Meta:
        model = Scheduler
        fields = ["app_name", "deploy_type", "schedule_dt"]
        widgets = {
            "deploy_type": forms.RadioSelect,
        }
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
            "deploy_type": forms.RadioSelect,
            #'deploy_type': forms.Select,
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['deploy_type'].widget.choices.pop(0)
