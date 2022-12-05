import datetime
from datetime import time

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
    create_deployment,
    get_app_deployment_service_info,
    change_service_select_bg_label,
    delete_deployment,
    update_deployment_scale,
)
from .forms import ClusterForm, AppInfoForm, DeployForm, DeployMethodForm
from .models import (
    AppInfo,
    Cluster,
    AppDeployHistory,
    AppDeployRevision,
    CanaryStategyMaster,
    CananryDeployHistory,
)
from api_utils.kubernetes_apis import parsing_kube_confing
from .forms import ClusterForm, AppInfoForm, DeployForm, DeployMethodForm, SchedulerForm
from .models import AppInfo, Cluster, AppDeployHistory, AppDeployRevision, Scheduler

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

def scheduler(request, pk):
    qs = Scheduler.objects.all()
    if qs:
        qs = qs.filter(app_name__app_name__exact=pk)
    return render(request, "app/scheduler.html", {"scheduler": qs})

@login_required
def schedule_list(request):
    qs = Cluster.objects.all()
    return render(request, "app/schedule_list.html", {"schedule_list": qs})


@login_required
def new_schedule(request):
    if request.method == "POST":
        form = SchedulerForm(request.POST, request.FILES)
        if form.is_valid():
            scheduler = Scheduler()
            scheduler.cluster_name = form.cleaned_data["cluster_name"]
            scheduler.kubeconfig = form.cleaned_data["kubeconfig"]
            scheduler.bearer_token = form.cleaned_data["bearer_token"]
            scheduler.user_id = request.user.id
            # scheduler, result_code, msg = chk_and_register_cluster(scheduler)
            if result_code == -1:
                messages.error(request, msg)
            else:
                messages.success(request, "클러스터 생성 성공.")
                cluster.save()
                return redirect("scheduler")
    else:
        form = SchedulerForm()
    return render(request, "app/new_schedule.html", {"form": form})


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
            return redirect("canary", pk=appinfo.app_name)
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
            appdeployrevision.before_replicas = deploy["replicas"]
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

            result_code, msg = create_deployment(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                deploy_name=deploy_name,
                namespace=namespace,
                image=image,
                replicas=appdeployrevision.before_replicas,
                labels=labels,
            )
            if result_code == 1:
                messages.success(request, msg)
                appdeployrevision.before_color = bef_label
                appdeployrevision.change_color = chg_label
                appdeployrevision.step = "DEPLOY"
                appdeployrevision.update_user = request.user.id
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
                    appdeployrevision.update_user = request.user.id
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
                    appdeployrevision.update_user = request.user.id
                    appdeployrevision.save()
                else:
                    messages.error(request, msg)
            if appdeployrevision.step == "DEPLOY":
                deploy_name = ""
                if appdeployrevision.before_color == "blue":
                    deploy_name = (
                        appdeployrevision.deployment[:-6]
                        + "green"
                        + "-"
                        + appdeployrevision.deployment[-1]
                    )
                elif appdeployrevision.before_color == "green":
                    deploy_name = (
                        appdeployrevision.deployment[:-5]
                        + "blue"
                        + "-"
                        + appdeployrevision.deployment[-1]
                    )

                result_code, msg = delete_deployment(
                    cluster_url=appdeployrevision.cluster_url,
                    cluster_token=appdeployrevision.cluster_token,
                    deploy_name=deploy_name,
                    namespace=appdeployrevision.namespace,
                )
                if result_code == 1:
                    appdeployrevision.step = "START"
                    appdeployrevision.update_user = request.user.id
                    appdeployrevision.save()
                else:
                    messages.error(request, msg)
            if appdeployrevision.step == "START":
                appdeployrevision.step = "ROLLBACK"
                appdeployrevision.update_user = request.user.id
                appdeployrevision.save()
                messages.success(request, "롤백 / 선택 취소 성공")
                return redirect("app_list")

        # Todo Kustomize 코드 변경 필요 (우선은 구현만 구현)
        elif "apply" in request.POST and appdeployrevision.step in ("CHANGE"):
            result_code, msg = delete_deployment(
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
        if last_revision.step not in ("DONE", "ROLLBACK"):
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
        app_revision.insert_user = request.user.id
        app_revision.update_user = request.user.id
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
    form.type = "BLUEGREEN"
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


@login_required
def canary(request, pk):
    appinfo = get_object_or_404(AppInfo, pk=pk)
    cluster = Cluster.objects.get(cluster_name=appinfo.cluster_name)
    canary_strategy = (
        CanaryStategyMaster.objects.all().distinct().values_list("sterategy")
    )
    canary_strategy_list = []
    for strategy in canary_strategy:
        canary_strategy_list.append(strategy[0])

    # Last revision check
    revision = AppDeployRevision.objects.filter(app_name=str(appinfo.app_name))
    if len(revision) > 0:
        revision_pk = revision.aggregate(Max("pk"))["pk__max"]
        last_revision = AppDeployRevision.objects.get(pk=revision_pk)
        if last_revision.step not in ("DONE", "ROLLBACK"):
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
        app_revision.deploy_type = "CANARY"
        app_revision.cluster_name = cluster.cluster_name
        app_revision.cluster_url = cluster.cluster_url
        app_revision.cluster_token = cluster.bearer_token
        app_revision.namespace = appinfo.namespace
        app_revision.deployment = request.POST["deployment"]
        app_revision.container = request.POST["container"]
        app_revision.tag = request.POST["version"]
        app_revision.step = "START"
        app_revision.insert_user = request.user.id
        app_revision.update_user = request.user.id
        app_revision.canary_sterategy = request.POST["canary_strategy"]
        if app_revision.deployment is None or len(app_revision.deployment.strip()) == 0:
            print("deployment isnone")
        elif app_revision.container is None or len(app_revision.container.strip()) == 0:
            print("container isnone")
        elif app_revision.tag is None or len(app_revision.tag.strip()) == 0:
            print("isnone")
        else:
            app_revision.save()
            revision = AppDeployRevision.objects.filter(
                app_name=str(app_revision.app_name)
            )
            revision_pk = revision.aggregate(Max("pk"))["pk__max"]

            canary_masters = CanaryStategyMaster.objects.filter(
                sterategy=app_revision.canary_sterategy
            )
            count = 0
            for canary_master in canary_masters:
                cananrydeployhistory = CananryDeployHistory()
                cananrydeployhistory.appdeployrevision_id = revision_pk
                cananrydeployhistory.sterategy = canary_master.sterategy
                cananrydeployhistory.Percentage = canary_master.Percentage
                cananrydeployhistory.step = canary_master.step
                cananrydeployhistory.timewait = canary_master.timewait
                if count == 0:
                    cananrydeployhistory.complete_yn = "D"
                elif cananrydeployhistory.timewait != 0:
                    cananrydeployhistory.complete_yn = "A"
                else:
                    cananrydeployhistory.complete_yn = "N"
                cananrydeployhistory.save()
                count += 1
            return redirect("canary_detail", pk=revision_pk, app_name=appinfo.app_name)

    form = DeployMethodForm()
    form.cluster_url = cluster.cluster_url
    form.cluster_token = cluster.bearer_token
    form.app_name = appinfo.app_name
    form.namespace = appinfo.namespace
    form.type = "CANARY"
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
        "app/canary.html",
        {
            "form": form,
            "app_name": appinfo.app_name,
            "namespace": appinfo.namespace,
            "canary_strategy": canary_strategy_list,
            "deploy_info": deploy_list,
            "container_info": container_list,
            "svc_dict": svc_dict,
        },
    )


@login_required
def canary_detail(request, pk, app_name):
    appdeployrevision = get_object_or_404(AppDeployRevision, pk=pk, app_name=app_name)
    canarydeployhistory = CananryDeployHistory.objects.filter(appdeployrevision_id=pk)
    result_code, msg, deploy = get_kubernetes_deployment(
        cluster_url=appdeployrevision.cluster_url,
        cluster_token=appdeployrevision.cluster_token,
        namespace=appdeployrevision.namespace,
        deployment=appdeployrevision.deployment,
    )
    if result_code == -1:
        messages.error(request, msg)
    present_replicaset = deploy["replicas"]
    if appdeployrevision.step in ("DONE", "ROLLBACK"):
        return redirect("app_list")
    elif appdeployrevision.step == "START":
        chg_replicaset = 0
        if appdeployrevision.before_replicas is None:
            appdeployrevision.before_replicas = deploy["replicas"]
            appdeployrevision.save()
            cur_replicaset = appdeployrevision.before_replicas
            max_replicaset = appdeployrevision.before_replicas + 1
            for canary in canarydeployhistory:
                percent = int(canary.Percentage)
                cur_v = cur_replicaset * percent / 100
                max_v = max_replicaset * percent / 100

                if abs(round(max_v, 0) - max_v) <= abs(round(cur_v, 0) - cur_v):
                    bef_replicaset = max_replicaset - round(max_v)
                    new_replicaset = round(max_v)
                else:
                    bef_replicaset = cur_replicaset - round(cur_v)
                    new_replicaset = round(cur_v)

                if bef_replicaset == 0:
                    bef_replicaset = 1
                    if new_replicaset == max_replicaset:
                        new_replicaset = cur_replicaset
                elif bef_replicaset == max_replicaset:
                    bef_replicaset = cur_replicaset
                elif new_replicaset == 0:
                    new_replicaset = 1
                    if new_replicaset == max_replicaset:
                        new_replicaset = cur_replicaset
                elif new_replicaset == max_replicaset:
                    new_replicaset = cur_replicaset

                if percent == 100:
                    bef_replicaset = 0
                    new_replicaset = cur_replicaset
                elif percent == 0:
                    bef_replicaset = cur_replicaset
                    new_replicaset = 0

                canary.real_percentage = round(
                    new_replicaset / (new_replicaset + bef_replicaset)
                )
                canary.pre_replicaset = bef_replicaset
                canary.new_replicaset = new_replicaset
                canary.save()
                print("save")
    else:
        result_code, msg, deploy = get_kubernetes_deployment(
            cluster_url=appdeployrevision.cluster_url,
            cluster_token=appdeployrevision.cluster_token,
            namespace=appdeployrevision.namespace,
            deployment=appdeployrevision.new_deployment,
        )
        if result_code == -1:
            messages.error(request, msg)
        chg_replicaset = deploy["replicas"]

    for canary in canarydeployhistory:
        if canary.complete_yn == "S":
            if canary.auto_deploy_time < datetime.datetime.now():
                canarydeploy = canary
                pre_replicaset = canarydeploy.pre_replicaset
                new_replicaset = canarydeploy.new_replicaset
                result_code = 1
                if pre_replicaset != present_replicaset:
                    result_code, msg = update_deployment_scale(
                        cluster_url=appdeployrevision.cluster_url,
                        cluster_token=appdeployrevision.cluster_token,
                        deploy_name=appdeployrevision.deployment,
                        namespace=appdeployrevision.namespace,
                        replicas=pre_replicaset,
                    )
                if result_code == 1:
                    if new_replicaset != chg_replicaset:
                        result_code, msg = update_deployment_scale(
                            cluster_url=appdeployrevision.cluster_url,
                            cluster_token=appdeployrevision.cluster_token,
                            deploy_name=appdeployrevision.new_deployment,
                            namespace=appdeployrevision.namespace,
                            replicas=new_replicaset,
                        )
                    if result_code == 1:
                        appdeployrevision.step = canarydeploy.step
                        appdeployrevision.update_user = request.user.id
                        appdeployrevision.save()
                        canarydeploy.complete_yn = "Y"
                        canarydeploy.save()
                        for canDeploy in canarydeployhistory:
                            if canDeploy.step == str(int(canarydeploy.step) + 1):
                                if canDeploy.complete_yn == "N":
                                    canDeploy.complete_yn = "W"
                                elif canDeploy.complete_yn == "A":
                                    canDeploy.complete_yn = "S"
                                    canDeploy.auto_deploy_time = (
                                        datetime.datetime.now()
                                        + datetime.timedelta(seconds=canDeploy.timewait)
                                    )
                            else:
                                continue
                            canDeploy.save()
                    else:
                        messages.error(request, msg)
                else:
                    messages.error(request, msg)

    if appdeployrevision.step == "ROLLBACK_BEF":
        if int(appdeployrevision.before_replicas) == int(deploy["readyReplicas"]):
            result_code, msg = delete_deployment(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                deploy_name=appdeployrevision.new_deployment,
                namespace=appdeployrevision.namespace,
            )
            if result_code != -1:
                appdeployrevision.step = "ROLLBACK"
                appdeployrevision.update_user = request.user.id
                appdeployrevision.save()
                messages.success(request, "롤백이 완료 되었습니다.")
                return redirect("app_list")

    if request.method == "POST":
        print(appdeployrevision.step)
        print(request.POST)
        if "deploy" in request.POST and appdeployrevision.step in ("START"):
            for canary in canarydeployhistory:
                if canary.complete_yn == "D":
                    present_replicaset = canary.pre_replicaset
                    new_replicaset = canary.new_replicaset
                else:
                    break
            deploy_name = appdeployrevision.deployment
            namespace = appdeployrevision.namespace
            image = appdeployrevision.container + ":" + appdeployrevision.tag
            labels = deploy["labels"]

            if labels["canary"] == "stable":
                deploy_name = deploy_name[:-1] + "c"
                labels["canary"] = "canary"
                bef_label = "stable"
                chg_label = "canary"
            elif labels["canary"] == "canary":
                deploy_name = deploy_name[:-1] + "s"
                labels["canary"] = "stable"
                bef_label = "canary"
                chg_label = "stable"

            print(labels)

            result_code, msg = create_deployment(
                cluster_url=appdeployrevision.cluster_url,
                cluster_token=appdeployrevision.cluster_token,
                deploy_name=deploy_name,
                namespace=namespace,
                image=image,
                replicas=new_replicaset,
                labels=labels,
            )
            if result_code == 1:
                messages.success(request, msg)
                appdeployrevision.before_color = bef_label
                appdeployrevision.change_color = chg_label
                appdeployrevision.new_deployment = deploy_name
                appdeployrevision.step = "DEPLOY"
                appdeployrevision.update_user = request.user.id
                appdeployrevision.save()
                if result_code == 1:
                    for cananryDeploy in canarydeployhistory:
                        if cananryDeploy.step == "1":
                            cananryDeploy.complete_yn = "Y"
                        elif cananryDeploy.step == "2":
                            if cananryDeploy.complete_yn == "N":
                                cananryDeploy.complete_yn = "W"
                            elif cananryDeploy.complete_yn == "A":
                                cananryDeploy.complete_yn = "S"
                                cananryDeploy.auto_deploy_time = (
                                    datetime.datetime.now()
                                    + datetime.timedelta(seconds=cananryDeploy.timewait)
                                )
                        else:
                            continue
                        cananryDeploy.save()
                    canarydeployhistory = CananryDeployHistory.objects.filter(
                        appdeployrevision_id=pk
                    )
                    if deploy["replicas"] != present_replicaset:
                        result_code, msg = update_deployment_scale(
                            cluster_url=appdeployrevision.cluster_url,
                            cluster_token=appdeployrevision.cluster_token,
                            deploy_name=appdeployrevision.deployment,
                            namespace=namespace,
                            replicas=present_replicaset,
                        )
                        if result_code == 1:
                            print("deployment update")
                        else:
                            messages.error(request, msg)

            else:
                messages.error(request, msg)
        elif "promote" in request.POST and appdeployrevision.step not in (
            "START",
            "DONE",
            "ROLLBACK",
        ):
            canarydeploy = canarydeployhistory.get(complete_yn="W")
            pre_replicaset = canarydeploy.pre_replicaset
            new_replicaset = canarydeploy.new_replicaset
            result_code = 1
            if pre_replicaset != present_replicaset:
                result_code, msg = update_deployment_scale(
                    cluster_url=appdeployrevision.cluster_url,
                    cluster_token=appdeployrevision.cluster_token,
                    deploy_name=appdeployrevision.deployment,
                    namespace=appdeployrevision.namespace,
                    replicas=pre_replicaset,
                )
            if result_code == 1:
                if new_replicaset != chg_replicaset:
                    result_code, msg = update_deployment_scale(
                        cluster_url=appdeployrevision.cluster_url,
                        cluster_token=appdeployrevision.cluster_token,
                        deploy_name=appdeployrevision.new_deployment,
                        namespace=appdeployrevision.namespace,
                        replicas=new_replicaset,
                    )
                if result_code == 1:
                    appdeployrevision.step = canarydeploy.step
                    appdeployrevision.update_user = request.user.id
                    appdeployrevision.save()
                    canarydeploy.complete_yn = "Y"
                    canarydeploy.save()
                    for canDeploy in canarydeployhistory:
                        if canDeploy.step == str(int(canarydeploy.step) + 1):
                            if canDeploy.complete_yn == "N":
                                canDeploy.complete_yn = "W"
                            elif canDeploy.complete_yn == "A":
                                canDeploy.complete_yn = "S"
                                canDeploy.auto_deploy_time = (
                                    datetime.datetime.now()
                                    + datetime.timedelta(seconds=canDeploy.timewait)
                                )
                        else:
                            continue
                        canDeploy.save()
                else:
                    messages.error(request, msg)
            else:
                messages.error(request, msg)

        elif "rollback" in request.POST and appdeployrevision.step not in ("DONE"):
            print(appdeployrevision.step)
            if appdeployrevision.step != "START":
                print(appdeployrevision.cluster_url)
                print(appdeployrevision.deployment)
                print(appdeployrevision.before_replicas)
                result_code, msg = update_deployment_scale(
                    cluster_url=appdeployrevision.cluster_url,
                    cluster_token=appdeployrevision.cluster_token,
                    deploy_name=appdeployrevision.deployment,
                    namespace=appdeployrevision.namespace,
                    replicas=int(appdeployrevision.before_replicas),
                )
                if result_code == 1:
                    messages.success(request, "롤백이 진행되고 있습니다. 잠시만 기다려주세요.")
                    appdeployrevision.step = "ROLLBACK_BEF"
                    appdeployrevision.save()
                else:
                    print(msg)
            for canarydeploy in canarydeployhistory:
                canarydeploy.complete_yn = "R"
                canarydeploy.save()
        elif "done" in request.POST and appdeployrevision.step not in ("DONE"):
            print("test2")

        canarydeployhistory = CananryDeployHistory.objects.filter(
            appdeployrevision_id=pk
        )
    return render(
        request,
        "app/canary_detail.html",
        {
            "appdeployrevision": appdeployrevision,
            "canarydeployhistory": canarydeployhistory,
            "present_replicaset": present_replicaset,
            "chg_replicaset": chg_replicaset,
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




