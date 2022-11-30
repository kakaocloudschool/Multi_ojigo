from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

from api_utils.argocd_apis import (
    get_request_with_bearer,
    create_argocd_cluster,
    get_argocd_token,
)
from api_utils.kubernetes_apis import parsing_kube_confing
from .forms import ClusterForm, AppInfoForm
from .models import AppInfo, Cluster

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
            file_content = cluster.kubeconfig.read().decode("utf-8")
            cluster_url, cluster_ca = parsing_kube_confing(file_content)
            if cluster_url != "-1" and cluster_ca != "-1":
                resp = get_request_with_bearer(cluster_url, cluster.bearer_token)
                if resp.status_code == 200:
                    cluster.cluster_url = cluster_url
                    cluster.user_id = request.user.id
                    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGO_PASSWORD)
                    if resp.status_code == 200:
                        argo_bearer_token = resp.json()["token"]
                        resp = create_argocd_cluster(
                            ARGOCD_URL,
                            argo_bearer_token,
                            cluster_url,
                            cluster.cluster_name,
                            cluster.bearer_token,
                            cluster_ca,
                        )
                        if resp.status_code == 200:
                            print("클러스터 생성 성공 ")
                            print(resp.text)
                            messages.success(request, 'Profile details updated.')

                            cluster.save()
                            return redirect("/")
                        else:
                            print("서버 생성 실패")
                            print(resp.text)
                            messages.warning(request, '서버 생성 실패')
                    else:
                        print("토큰 발급 실패")
                        messages.warning(request, '토큰발급실패')
                else:
                    print("파일 또는 토큰 확인 필요")
                    messages.warning(request, '파일 또는 토큰 확인 필요')
            else:
                print("kubernetes config 파일이 아닙니다")
                messages.error(request, 'kubernetes config 파일이 아닙니다')
    else:
        form = ClusterForm()

    return render(request, "app/cluster_add.html", {"form": form})


@login_required
def new_app(request):
    if request.method == "POST":
        form = AppInfoForm(request.POST, request.FILES)
        if form.is_valid():
            appinfo = form.save(commit=False)
            return redirect("/")
    else:
        form = AppInfoForm()

    return render(request, "app/cluster_add.html", {"form": form})
