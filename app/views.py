from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from api_utils.argocd_apis import (
    chk_and_register_cluster,
    del_argocd_cluster,
    create_argocd_app_check,
    del_argocd_app,
)
from api_utils.kubernetes_apis import parsing_kube_confing
from .forms import ClusterForm, AppInfoForm, DeployForm
from .models import AppInfo, Cluster, AppDeployHistory

ARGOCD_URL = getattr(settings, "ARGOCD_URL", None)
ARGOCD_USERNAME = getattr(settings, "ARGOCD_USERNAME", None)
ARGO_PASSWORD = getattr(settings, "ARGO_PASSWORD", None)

# Create your views here.
@login_required
def cluster_list(request):
    qs = Cluster.objects.all()
    return render(request, "app/cluster_list.html", {"cluster_list": qs})


@login_required
def app_list(request):
    qs = AppInfo.objects.all()
    return render(request, "index.html", {"appinfo_list": qs})


# Todo - 임시 중첩 if 문 작성 -> 에러 메세지 처리 나온 이후에는, 변환할 것.
@login_required
def new_cluster(request):
    if request.method == "POST":
        form = ClusterForm(request.POST, request.FILES)
        if form.is_valid():
            cluster = Cluster()
            cluster.cluster_name = form.cleaned_data["cluster_name"]
            cluster.kubeconfig = form.cleaned_data["kubeconfig"]
            cluster.bearer_token = form.cleaned_data["bearer_token"]
            cluster.user_id = request.user.id
            cluster, result_code, msg = chk_and_register_cluster(cluster)
            if result_code == -1:
                messages.error(request, msg)
            else:
                messages.success(request, "클러스터 생성 성공.")
                cluster.save()
                return redirect("cluster_list")
    else:
        form = ClusterForm()

    return render(request, "app/write_form.html", {"form": form})


@login_required
def new_app(request):
    if request.method == "POST":
        form = AppInfoForm(request.POST)  # form 정보 가져옴
        if form.is_valid():
            appinfo = AppInfo()
            appinfo.app_name = form.cleaned_data["app_name"]
            appinfo.cluster_name = form.cleaned_data["cluster_name"]
            appinfo.auto_create_ns = form.cleaned_data["auto_create_ns"]
            appinfo.namespace = form.cleaned_data["namespace"]
            appinfo.repo_url = form.cleaned_data["repo_url"]
            appinfo.target_revision = form.cleaned_data["target_revision"]
            appinfo.target_path = form.cleaned_data["target_path"]
            cluster = Cluster.objects.get(cluster_name=appinfo.cluster_name)
            cluster_url = cluster.cluster_url
            cluster_token = cluster.bearer_token
            result_code, msg = create_argocd_app_check(
                cluster_url=cluster_url,
                cluster_token=cluster_token,
                auto_create_ns=appinfo.auto_create_ns,
                app_name=appinfo.app_name,
                namespace=appinfo.namespace,
                repo_url=appinfo.repo_url,
                target_revision=appinfo.target_revision,
                target_path=appinfo.target_path,
            )
            print(result_code, msg)
            if result_code == -1:
                messages.error(request, msg)
            else:
                appinfo.update_user = request.user.id
                appinfo.insert_user = request.user.id
                appinfo.save()
                messages.success(request, f"{appinfo.app_name} 앱 생성 성공.")
                return redirect("app_list")
    else:
        form = AppInfoForm()
    return render(request, "app/write_form.html", {"form": form})


@login_required
def del_cluster(request, slug):
    cluster = get_object_or_404(Cluster, cluster_name=slug)
    if del_argocd_cluster(cluster.cluster_url):
        cluster.delete()
    else:
        messages.error(request, "cluster 삭제 실패")
    return redirect("cluster_list")


# push


@login_required
def delete_app(request, pk):
    appinfo = get_object_or_404(AppInfo, pk=pk)
    if del_argocd_app(appinfo.app_name):
        messages.success(request, f"{appinfo.app_name} 앱 삭제 완료")
        appinfo.delete()
    else:
        messages.error(request, f"{appinfo.app_name} 앱 삭제 실패")
    return redirect("app_list")


# push
@login_required
def deploy_app(request, pk):
    appinfo = get_object_or_404(AppInfo, pk=pk)
    form = DeployForm(request.POST)  # form 정보 가져옴

    if form.is_valid():
        deploy = AppDeployHistory()  # model 정보 가져옴
        deploy.app_name = appinfo
        deploy.revision = appinfo.target_revision
        deploy.deploy_type = form.cleaned_data["deploy_type"]
        deploy.user = request.user.id
        deploy.manager_user = request.user.id
        deploy.save()
        if deploy.deploy_type == "RollingUpdate":
            return render(request, "app/rollingupdate.html")
        elif deploy.deploy_type == "BlueGreen":
            return render(request, "app/bluegreen.html")
        elif deploy.deploy_type == "Canary":
            return render(request, "app/canary.html")

    return render(request, "app/app_deploy.html", {"form": form})


# !수정
@login_required
def history_app(request,q):
    qs = AppDeployHistory.objects.all()
    #q = request.GET.get("q", "")
    if qs:
        qs = qs.filter(app_name__app_name__=q)
    return render(request, "app/deploy_history.html", {"deploy_history": qs})
