from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from api_utils.argocd_apis import (
    chk_and_register_cluster,
    del_argocd_cluster,
    create_argocd_app_check,
    del_argocd_app,
)
from .forms import ClusterForm, AppInfoForm
from .models import AppInfo, Cluster

# Create your views here.
@login_required
def cluster_list(request):
    qs = Cluster.objects.all()
    return render(request, "app/cluster_list.html", {"cluster_list": qs})


@login_required
def app_list(request):
    qs = AppInfo.objects.all()
    return render(request, "index.html", {"appinfo_list": qs})


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
    context = {}
    appinfo = get_object_or_404(AppInfo, pk=pk)
    if del_argocd_app(appinfo.app_name):
        messages.success(request, f"{appinfo.app_name} 앱 삭제 완료")
        appinfo.delete()
    else:
        messages.error(request, f"{appinfo.app_name} 앱 삭제 실패")
    return redirect("app_list")


@login_required
def deploy_app(request):
    if request.method == "POST":
        form = AppInfoForm(request.POST)  # form 정보 가져옴
        if form.is_valid():
            appinfo = AppInfo()  # model 정보 가져옴
            appinfo.app_name = form.cleaned_data["app_name"]
            appinfo.cluster_name = form.cleaned_data["cluster_name"]
            appinfo.auto_create_ns = form.cleaned_data["auto_create_ns"]
            appinfo.namespace = form.cleaned_data["namespace"]
            appinfo.repo_url = form.cleaned_data["repo_url"]
            appinfo.target_revision = form.cleaned_data["target_revision"]
            appinfo.target_path = form.cleaned_data["target_path"]
            appinfo = form.save(commit=False)  # DB에 바로 저장하지 않고 form으로 작업하기 위해 임시로 저장
            appinfo.save()
            return redirect("/")
    else:
        form = AppInfoForm()

    return render(request, "app/appinfo_deploy.html", {"form": form})


@login_required
def history_app(request):
    qs = AppInfo.objects.all()
    return render(request, "app/appinfo_history.html", {"appinfo_list": qs})
