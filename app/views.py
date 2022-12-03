from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from api_utils.argocd_apis import (
    chk_and_register_cluster,
    del_argocd_cluster,
    create_argocd_app_check,
    del_argocd_app,
    get_app_deploy_and_service_info,
    post_rolling_update_sync,
    get_kubernetes_deployment,
    create_deployment_bluegreen,
    get_app_deployment_service_info,
    change_service_select_bg_label,
    delete_deployment_bluegreen,
)
from api_utils.kubernetes_apis import parsing_kube_confing
from .forms import ClusterForm, AppInfoForm, DeployForm, DeployMethodForm
from .models import AppInfo, Cluster, AppDeployHistory, AppDeployRevision

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
    # Last revision check
    revision = AppDeployRevision.objects.filter(app_name=str(appinfo.app_name))
    if len(revision) > 0:
        revision_pk = revision.aggregate(Max("pk"))["pk__max"]
        last_revision = AppDeployRevision.objects.get(pk=revision_pk)
        if last_revision.step not in ("START", "DONE", "ROLLBACK"):
            if last_revision.deploy_type == "BLUEGREEN":
                messages.info(request, "진행 중인 배포 작업이 있습니다.")
                return redirect(
                    "bluegreen_detail",
                    pk=last_revision.pk,
                    app_name=str(appinfo.app_name),
                )
            elif last_revision.deploy_type == "CANARY":
                messages.info(request, "진행 중인 배포 작업이 있습니다.")
                return redirect(
                    "canary_detail",
                    pk=last_revision.pk,
                    app_name=str(appinfo.app_name),
                )
    if form.is_valid():
        if form.cleaned_data["deploy_type"] == "RollingUpdate":
            return redirect("rollingupdate", pk=appinfo.app_name)
        elif form.cleaned_data["deploy_type"] == "BlueGreen":
            return redirect("bluegreen", pk=appinfo.app_name)
        elif form.cleaned_data["deploy_type"] == "Canary":
            return render(request, "app/canary.html", {"appinfo": appinfo})

    return render(request, "app/app_deploy.html", {"form": form})


@login_required
def rollingupdate(request, pk):
    appinfo = get_object_or_404(AppInfo, pk=pk)
    cluster = Cluster.objects.get(cluster_name=appinfo.cluster_name)
    # Last revision check
    revision = AppDeployRevision.objects.filter(app_name=str(appinfo.app_name))
    if len(revision) > 0:
        revision_pk = revision.aggregate(Max("pk"))["pk__max"]
        last_revision = AppDeployRevision.objects.get(pk=revision_pk)
        if last_revision.step not in ("START", "DONE", "ROLLBACK"):
            if last_revision.deploy_type == "BLUEGREEN":
                messages.info(request, "진행 중인 배포 작업이 있습니다.")
                return redirect(
                    "bluegreen_detail",
                    pk=last_revision.pk,
                    app_name=str(appinfo.app_name),
                )
            elif last_revision.deploy_type == "CANARY":
                messages.info(request, "진행 중인 배포 작업이 있습니다.")
                return redirect(
                    "canary_detail",
                    pk=last_revision.pk,
                    app_name=str(appinfo.app_name),
                )
    print(request.method)
    if request.method == "POST":
        print(request.POST)
        if "rolling_deploy" in request.POST:
            result_code, msg = post_rolling_update_sync(appinfo.app_name)
            if result_code == -1:
                messages.error(request, msg)
            else:
                messages.success(request, msg)

    return render(
        request,
        "app/rollingupdate.html",
        {"appinfo": appinfo},
    )


@login_required
def bluegreen_detail(request, pk, app_name):
    appdeployrevision = get_object_or_404(AppDeployRevision, pk=pk, app_name=app_name)
    if appdeployrevision.step in ("DONE", "ROLLBACK"):
        return redirect("app_list")
    if request.method == "POST":
        print(appdeployrevision.step)
        print(request.POST)
        if "deploy" in request.POST and appdeployrevision.step in ("START"):
            result_code, msg, deploy = get_kubernetes_deployment(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                namespace=appdeployrevision.namespace,
                deployment=appdeployrevision.deployment,
            )
            if result_code == -1:
                messages.error(request, msg)
                return render(
                    request,
                    "app/bluegreen_detail.html",
                    {"appdeployrevision": appdeployrevision},
                )
            deploy_name = appdeployrevision.deployment
            namespace = appdeployrevision.namespace
            image = appdeployrevision.container + ":" + appdeployrevision.tag
            replicas = deploy["replicas"]
            labels = deploy["labels"]
            if labels["bluegreen"] == "blue":
                deploy_name = deploy_name[:-4] + "green"
                labels["bluegreen"] = "green"
                bef_label = "blue"
                chg_label = "green"

            elif labels["bluegreen"] == "green":
                deploy_name = deploy_name[:-5] + "blue"
                labels["bluegreen"] = "blue"
                bef_label = "green"
                chg_label = "blue"

            result_code, msg = create_deployment_bluegreen(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                deploy_name=deploy_name,
                namespace=namespace,
                image=image,
                replicas=replicas,
                labels=labels,
            )
            if result_code == 1:
                messages.success(request, msg)
                appdeployrevision.before_color = bef_label
                appdeployrevision.change_color = chg_label
                appdeployrevision.step = "DEPLOY"
                appdeployrevision.save()
            else:
                messages.error(request, msg)
        elif "change" in request.POST and appdeployrevision.step in ("DEPLOY"):
            result_code, msg, service_name, label = get_app_deployment_service_info(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                app_name=appdeployrevision.app_name,
                namespace=appdeployrevision.namespace,
                target_deployment=appdeployrevision.deployment,
            )
            if result_code == 1:
                if label == "blue":
                    label = "green"
                else:
                    label = "blue"
                result_code, msg = change_service_select_bg_label(
                    cluster_url=appdeployrevision.cluster_url,
                    cluster_token=appdeployrevision.cluster_token,
                    service_name=service_name,
                    namespace=appdeployrevision.namespace,
                    bg_label=label,
                )
                if result_code == 1:
                    messages.success(request, msg)
                    appdeployrevision.target_service = service_name
                    appdeployrevision.step = "CHANGE"
                    appdeployrevision.save()
                else:
                    messages.error(request, msg)
            else:
                messages.error(request, msg)
        elif "rollback" in request.POST and appdeployrevision.step in (
            "DEPLOY",
            "CHANGE",
            "START",
        ):
            if appdeployrevision.step == "CHANGE":
                result_code, msg = change_service_select_bg_label(
                    cluster_url=appdeployrevision.cluster_url,
                    cluster_token=appdeployrevision.cluster_token,
                    service_name=appdeployrevision.target_service,
                    namespace=appdeployrevision.namespace,
                    bg_label=appdeployrevision.before_color,
                )
                if result_code == 1:
                    messages.success(request, msg)
                    appdeployrevision.step = "DEPLOY"
                    appdeployrevision.save()
                else:
                    messages.error(request, msg)
            if appdeployrevision.step == "DEPLOY":
                deploy_name = ""
                if appdeployrevision.before_color == "blue":
                    deploy_name = appdeployrevision.deployment[:-4] + "green"
                elif appdeployrevision.before_color == "green":
                    deploy_name = appdeployrevision.deployment[:-5] + "blue"

                result_code, msg = delete_deployment_bluegreen(
                    cluster_url=appdeployrevision.cluster_url,
                    cluster_token=appdeployrevision.cluster_token,
                    deploy_name=deploy_name,
                    namespace=appdeployrevision.namespace,
                )
                if result_code == 1:
                    appdeployrevision.step = "START"
                    appdeployrevision.save()
                else:
                    messages.error(request, msg)
            if appdeployrevision.step == "START":
                appdeployrevision.step = "ROLLBACK"
                appdeployrevision.save()
                messages.success(request, "롤백 / 선택 취소 성공")
                return redirect("app_list")

        # Todo Kustomize 코드 변경 필요 (우선은 구현만 구현)
        elif "apply" in request.POST and appdeployrevision.step in ("CHANGE"):
            result_code, msg = delete_deployment_bluegreen(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                deploy_name=appdeployrevision.deployment,
                namespace=appdeployrevision.namespace,
            )
            if result_code == 1:
                messages.success(request, "적용 완료")
                appdeployrevision.step = "DONE"
                appdeployrevision.save()
                return redirect("app_list")
            else:
                messages.error(request, msg)
    return render(
        request,
        "app/bluegreen_detail.html",
        {"appdeployrevision": appdeployrevision},
    )


@login_required
def bluegreen(request, pk):
    appinfo = get_object_or_404(AppInfo, pk=pk)
    cluster = Cluster.objects.get(cluster_name=appinfo.cluster_name)
    # Last revision check
    revision = AppDeployRevision.objects.filter(app_name=str(appinfo.app_name))
    if len(revision) > 0:
        revision_pk = revision.aggregate(Max("pk"))["pk__max"]
        last_revision = AppDeployRevision.objects.get(pk=revision_pk)
        if last_revision.step not in ("START", "DONE", "ROLLBACK"):
            if last_revision.deploy_type == "BLUEGREEN":
                messages.info(request, "진행 중인 배포 작업이 있습니다.")
                return redirect(
                    "bluegreen_detail",
                    pk=last_revision.pk,
                    app_name=str(appinfo.app_name),
                )
            elif last_revision.deploy_type == "CANARY":
                messages.info(request, "진행 중인 배포 작업이 있습니다.")
                return redirect(
                    "canary_detail",
                    pk=last_revision.pk,
                    app_name=str(appinfo.app_name),
                )
    if request.method == "POST":
        app_revision = AppDeployRevision()
        app_revision.app_name = appinfo.app_name
        app_revision.deploy_type = "BLUEGREEN"
        app_revision.cluster_name = cluster.cluster_name
        app_revision.cluster_url = cluster.cluster_url
        app_revision.cluster_token = cluster.bearer_token
        app_revision.namespace = appinfo.namespace
        app_revision.deployment = request.POST["deployment"]
        app_revision.container = request.POST["container"]
        app_revision.tag = request.POST["version"]
        app_revision.step = "START"
        if app_revision.tag is None or len(app_revision.tag.strip()) == 0:
            print("isnone")
        else:
            app_revision.save()
            revision = AppDeployRevision.objects.filter(
                app_name=str(app_revision.app_name)
            )
            revision_pk = revision.aggregate(Max("pk"))["pk__max"]
            return redirect(
                "bluegreen_detail", pk=revision_pk, app_name=appinfo.app_name
            )

    form = DeployMethodForm()
    form.cluster_url = cluster.cluster_url
    form.cluster_token = cluster.bearer_token
    form.app_name = appinfo.app_name
    form.namespace = appinfo.namespace
    form.type = "bluegreen"
    deploy_list = []
    container_list = []
    result_code, msg, deploy_info_dict, svc_dict = get_app_deploy_and_service_info(
        cluster_url=form.cluster_url,
        cluster_token=form.cluster_token,
        app_name=appinfo.app_name,
    )
    if result_code == -1:
        messages.error(request, msg)
        redirect("/")
    else:
        for deploy in deploy_info_dict:
            deploy_list.append(deploy)
            for container in deploy_info_dict[deploy]["image"]:
                container_list.append(
                    {"deploy": deploy, "image": container.split(":")[0]}
                )
    return render(
        request,
        "app/bluegreen.html",
        {
            "form": form,
            "app_name": appinfo.app_name,
            "namespace": appinfo.namespace,
            "deploy_info": deploy_list,
            "container_info": container_list,
            "svc_dict": svc_dict,
        },
    )


# !수정
@login_required
def history_app(request, q):
    qs = AppDeployHistory.objects.all()
    # q = request.GET.get("q", "")
    if qs:
        qs = qs.filter(app_name__app_name__exact=q)
    return render(request, "app/deploy_history.html", {"deploy_history": qs})


def test_web(request):
    return render(request, "test.html")
