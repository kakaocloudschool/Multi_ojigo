import requests
from requests.structures import CaseInsensitiveDict
import json
from .kubernetes_apis import (
    is_have_namespace,
    create_namespace_in_cluster,
    parsing_kube_confing,
)
from django.conf import settings


ARGOCD_URL = getattr(settings, "ARGOCD_URL", None)
ARGOCD_USERNAME = getattr(settings, "ARGOCD_USERNAME", None)
ARGO_PASSWORD = getattr(settings, "ARGO_PASSWORD", None)


def get_argocd_token(
    url: str, username: str, password: str
) -> requests.models.Response:
    url = url + "api/v1/session"

    data = {"username": username, "password": password}
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    return resp


def get_request_with_bearer(url: str, bearer_token: str) -> requests.models.Response:
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {bearer_token}"
    print("test3")
    resp = requests.get(url, headers=headers, verify=False)
    print("test4")
    return resp


def create_argocd_cluster(
    argo_url: str,
    argo_bearer_token: str,
    cluster_server: str,
    cluster_name: str,
    cluster_token: str,
    cluster_ca: str,
):
    url = argo_url + "api/v1/clusters"

    data = {
        "server": cluster_server,
        "name": cluster_name,
        "config": {
            "bearerToken": cluster_token,
            "tlsClientConfig": {"insecure": False, "caData": cluster_ca},
        },
    }
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    return resp


def create_argocd_app_with_auto_create_namespace(
    argocd_url: str,
    argo_bearer_token: str,
    app_name: str,
    namespace: str,
    repo_url: str,
    target_revision: str,
    target_path: str,
    cluster_url: str,
    cluster_token: str,
):
    if not is_have_namespace(cluster_url, cluster_token, namespace):
        create_namespace_in_cluster(cluster_url, cluster_token, namespace)
    return create_argocd_app(
        argocd_url=argocd_url,
        argo_bearer_token=argo_bearer_token,
        app_name=app_name,
        namespace=namespace,
        repo_url=repo_url,
        target_path=target_path,
        target_revision=target_revision,
        cluster_url=cluster_url,
    )


def create_argocd_app(
    argocd_url: str,
    argo_bearer_token: str,
    app_name: str,
    namespace: str,
    repo_url: str,
    target_revision: str,
    target_path: str,
    cluster_url: str,
):

    url = argocd_url + "api/v1/applications"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"
    data = {
        "metadata": {"name": app_name, "namespace": "argocd"},
        "spec": {
            "project": "default",
            "source": {
                "repoURL": repo_url,
                "targetRevision": target_revision,
                "path": target_path,
            },
            "destination": {"server": cluster_url[:-1], "namespace": namespace},
        },
    }
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    if resp.status_code != 200:
        return -1, "앱 등록 정보가 불일치 하거나, 이미 등록된 정보 입니다."
    return 1, "앱 등록이 완료 되었습니다."


def chk_and_register_cluster(cluster):
    try:
        file_content = cluster.kubeconfig.read().decode("utf-8")
        cluster_url, cluster_ca = parsing_kube_confing(file_content)
    except:
        return cluster, -1, "읽을 수 없는 파일입니다."

    if cluster_url == "-1" or cluster_ca == "-1":
        return cluster, -1, "kubernetes config 파일이 아닙니다"

    resp = get_request_with_bearer(cluster_url, cluster.bearer_token)

    if resp.status_code != 200:
        return cluster, -1, "쿠버네티스 서버에 접근이 불가합니다."

    cluster.cluster_url = cluster_url
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGO_PASSWORD)

    if resp.status_code != 200:
        return cluster, -1, "Argo CD 서버에 접근이 불가합니다."
    argo_bearer_token = resp.json()["token"]
    resp = create_argocd_cluster(
        ARGOCD_URL,
        argo_bearer_token,
        cluster_url,
        cluster.cluster_name,
        cluster.bearer_token,
        cluster_ca,
    )
    if resp.status_code != 200:
        return cluster, -1, "이미 클러스터에 등록된 서버이거나, 확인이 필요합니다. 관리자에게 문의하세요."

    return cluster, 1, "클러스터 생성에 성공하였습니다. "


def del_argocd_cluster(cluster_url):
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGO_PASSWORD)
    argo_bearer_token = resp.json()["token"]
    url = ARGOCD_URL + "api/v1/clusters/" + cluster_url
    print(url)
    print(argo_bearer_token)

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"

    resp = requests.delete(url, headers=headers, verify=False)
    print(resp.text)
    if resp.status_code == 200:
        return True
    else:
        return False


def create_argocd_app_check(
    cluster_url,
    cluster_token,
    auto_create_ns,
    app_name,
    namespace,
    repo_url,
    target_revision,
    target_path,
):
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGO_PASSWORD)
    if resp.status_code != 200:
        return -1, "배포 서버의 토큰 발급에 실패하였습니다."
    argo_bearer_token = resp.json()["token"]

    if auto_create_ns:
        return create_argocd_app_with_auto_create_namespace(
            argocd_url=ARGOCD_URL,
            argo_bearer_token=argo_bearer_token,
            app_name=app_name,
            namespace=namespace,
            repo_url=repo_url,
            target_revision=target_revision,
            target_path=target_path,
            cluster_url=cluster_url,
            cluster_token=cluster_token,
        )
    else:
        return create_argocd_app(
            argocd_url=ARGOCD_URL,
            argo_bearer_token=argo_bearer_token,
            app_name=app_name,
            namespace=namespace,
            repo_url=repo_url,
            target_path=target_path,
            target_revision=target_revision,
            cluster_url=cluster_url,
        )
