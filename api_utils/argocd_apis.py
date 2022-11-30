import requests
from requests.structures import CaseInsensitiveDict
import json
from .kubernetes_apis import is_have_namespace, create_namespace_in_cluster


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
            "destination": {"server": cluster_url, "namespace": namespace},
        },
    }
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    print(resp.text)
