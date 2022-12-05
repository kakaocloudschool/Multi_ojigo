import requests
from requests.structures import CaseInsensitiveDict
import json
from .kubernetes_apis import (
    is_have_namespace,
    create_namespace_in_cluster,
    parsing_kube_confing,
)

from django.conf import settings
from collections import defaultdict

# ARGOCD_URL = "https://192.168.50.104/"
# ARGOCD_USERNAME = "admin"
# ARGOCD_PASSWORD = "hHGfeDCRrCJ2pXCP"
ARGOCD_URL = getattr(settings, "ARGOCD_URL", None)
ARGOCD_USERNAME = getattr(settings, "ARGOCD_USERNAME", None)
ARGOCD_PASSWORD = getattr(settings, "ARGO_PASSWORD", None)


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
    resp = requests.get(url, headers=headers, verify=False)
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
    if resp.status_code not in (200, 201):
        print(resp.status_code, resp.text)
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

    if resp.status_code != 200 and resp.status_code != 201:
        return cluster, -1, "쿠버네티스 서버에 접근이 불가합니다."

    cluster.cluster_url = cluster_url
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)

    if resp.status_code != 200 and resp.status_code != 201:
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
    if resp.status_code != 200 and resp.status_code != 201:
        return cluster, -1, "이미 클러스터에 등록된 서버이거나, 확인이 필요합니다. 관리자에게 문의하세요."

    return cluster, 1, "클러스터 생성에 성공하였습니다. "


def del_argocd_cluster(cluster_url):
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)
    argo_bearer_token = resp.json()["token"]
    url = ARGOCD_URL + "api/v1/clusters/" + cluster_url

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"

    resp = requests.delete(url, headers=headers, verify=False)
    if resp.status_code == 200:
        return True
    else:
        return False


def del_argocd_app(app_name):
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)
    argo_bearer_token = resp.json()["token"]
    url = ARGOCD_URL + "api/v1/applications/" + app_name
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"
    resp = requests.delete(url, headers=headers, verify=False)
    if resp.status_code == 200:
        return True
    else:
        print(resp.text)
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
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)
    if resp.status_code != 200 and resp.status_code != 201:
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


def get_argo_service_deployment_name(
    argocd_url: str, argo_bearer_token: str, app_name: str
):
    url = argocd_url + "/api/v1/applications/" + app_name + "/resource-tree"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"
    resp = requests.get(url, headers=headers, verify=False)
    deployment_dict = defaultdict(list)
    service_dict = defaultdict(list)
    json_resp = resp.json()
    for resource in json_resp["nodes"]:
        if resource["kind"] == "Deployment":
            deployment_dict[resource["namespace"]].append(resource["name"])
        if resource["kind"] == "Service":
            service_dict[resource["namespace"]].append(resource["name"])
    return deployment_dict, service_dict


def get_kubernetes_deployment(
    cluster_url: str, cluster_token: str, namespace: str, deployment: str
):
    url = (
        cluster_url
        + "apis/apps/v1/namespaces/"
        + namespace
        + "/deployments/"
        + deployment
    )
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.get(url, headers=headers, verify=False)
    deploy = {}
    if resp.status_code not in (200, 201):
        return -1, "디플로이먼트 조회 실패", deploy
    json_resp = resp.json()
    deploy["name"] = deployment
    deploy["namespace"] = namespace
    deploy["cluster_url"] = cluster_url
    deploy["labels"] = json_resp["metadata"]["labels"]
    deploy["replicas"] = json_resp["spec"]["replicas"]
    if deploy["replicas"] == 0:
        deploy["readyReplicas"] = 0
    else:
        deploy["readyReplicas"] = json_resp["status"]["readyReplicas"]
    deploy["image"] = []
    for container in json_resp["spec"]["template"]["spec"]["containers"]:
        deploy["image"].append(container["image"])
    return 1, "디플로이먼트 조회 성공", deploy


def get_kubernetes_service(
    cluster_url: str, cluster_token: str, namespace: str, service: str
):
    url = cluster_url + "api/v1/namespaces/" + namespace + "/services/" + service
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.get(url, headers=headers, verify=False)
    service_dic = {}
    if resp.status_code != 200:
        return -1, "서비스 조회 실패", service_dic
    json_resp = resp.json()
    service_dic["name"] = service
    service_dic["namespace"] = namespace
    service_dic["cluster_url"] = cluster_url
    service_dic["labels"] = json_resp["spec"]["selector"]
    return 1, "서비스 조회 성공", service_dic


def post_rolling_update_sync(app_name):
    print(1)
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)
    if resp.status_code in (200, 201):
        argo_bearer_token = resp.json()["token"]
    else:
        return -1, "argo 토큰 발급 실패"
    url = str(ARGOCD_URL) + "api/v1/applications/" + str(app_name) + "/sync"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {argo_bearer_token}"
    resp = requests.post(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return -1, "롤링 업데이트 전송 실패"
    else:
        return 1, "롤링 업데이트 전송 성공"


def get_app_deploy_and_service_info(cluster_url, cluster_token, app_name):
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)
    argo_bearer_token = ""
    # 토큰 발급 실패면, 에러 팝업
    if resp.status_code in (200, 201):
        argo_bearer_token = resp.json()["token"]
    else:
        print(resp.status_code, resp.text)
        return -1, "argo 토큰 발급 실패", {}, {}
    name_deploy_dict, service_dict = get_argo_service_deployment_name(
        ARGOCD_URL, argo_bearer_token, app_name
    )
    deploy_info_dict = {}
    svc_dict = {}

    is_have_deployment = False

    for namespace, deployments in name_deploy_dict.items():
        for deployment in deployments:
            result_code, msg, deploy = get_kubernetes_deployment(
                cluster_url=cluster_url,
                cluster_token=cluster_token,
                namespace=namespace,
                deployment=deployment,
            )
            if result_code != 1:
                continue
            if deploy["replicas"] != 0:
                deploy_info_dict[deployment] = deploy
                is_have_deployment = True
    if not is_have_deployment:
        return -1, "디플로이먼트가 존재하지 않거나, 조회에 실패하였습니다. ", {}, {}

    for namespace, services in service_dict.items():
        for service in services:
            result_code, msg, svc = get_kubernetes_service(
                cluster_url=cluster_url,
                cluster_token=cluster_token,
                namespace=namespace,
                service=service,
            )
            svc_dict[service] = svc
            if result_code != 1:
                return -1, msg, {}, {}

    return 1, "서비스 조회 성공", deploy_info_dict, svc_dict


def get_app_deployment_service_info(
    cluster_url, cluster_token, app_name, namespace, target_deployment
):
    resp = get_argocd_token(ARGOCD_URL, ARGOCD_USERNAME, ARGOCD_PASSWORD)
    argo_bearer_token = ""
    # 토큰 발급 실패면, 에러 팝업
    if resp.status_code in (200, 201):
        argo_bearer_token = resp.json()["token"]
    else:
        print(resp.status_code, resp.text)
        return -1, "argo 토큰 발급 실패", ""
    name_deploy_dict, service_dict = get_argo_service_deployment_name(
        ARGOCD_URL, argo_bearer_token, app_name
    )
    svc_dict = {}
    result_code, msg, deploy = get_kubernetes_deployment(
        cluster_url=cluster_url,
        cluster_token=cluster_token,
        namespace=namespace,
        deployment=target_deployment,
    )
    taget_labels = deploy["labels"]
    print(taget_labels)

    for namespace, services in service_dict.items():
        for service in services:
            result_code, msg, svc = get_kubernetes_service(
                cluster_url=cluster_url,
                cluster_token=cluster_token,
                namespace=namespace,
                service=service,
            )
            svc_dict[service] = svc
            if result_code != 1:
                return -1, msg, ""
            print(svc_dict[service]["labels"])
            match = True
            for label in svc_dict[service]["labels"]:
                if taget_labels[label] != svc_dict[service]["labels"][label]:
                    match = False
                    print("no")
            if match == True:
                return 1, "서비스 조회 성공", service, svc_dict[service]["labels"]["bluegreen"]
    return -1, "서비스 조회 실패", "", ""


def get_deployment_replicas(
    cluster_url, cluster_token, namespace, deploy_name, replicas
):
    url = (
        cluster_url
        + "apis/apps/v1/namespaces/"
        + namespace
        + "/deployments/"
        + deploy_name
    )
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return -1, "디플로이먼트 조회 실패", 0
    resp_json = resp.json()
    ready_replicas = resp_json["status"]["readyReplicas"]
    return 1, "디플로이먼트 조회 성공", ready_replicas


def update_deployment_scale(
    cluster_url, cluster_token, namespace, deploy_name, replicas
):
    url = (
        cluster_url
        + "apis/apps/v1/namespaces/"
        + namespace
        + "/deployments/"
        + deploy_name
    )
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return -1, "디플로이먼트 조회 실패"
    resp_json = resp.json()
    resp_json["spec"]["replicas"] = replicas

    url = (
        cluster_url
        + "apis/apps/v1/namespaces/"
        + namespace
        + "/deployments/"
        + deploy_name
    )
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.put(url, headers=headers, data=json.dumps(resp_json), verify=False)
    if resp.status_code != 200 and resp.status_code != 201:
        return -1, "디플로이먼트 조회 실패"
    return 1, "디플로이먼트 변경 성공"


def create_deployment(
    cluster_url, cluster_token, deploy_name, namespace, image, replicas, labels
):
    url = cluster_url + "apis/apps/v1/namespaces/" + namespace + "/deployments"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    data = {
        "kind": "Deployment",
        "apiVersion": "apps/v1",
        "metadata": {
            "name": deploy_name,
            "namespace": namespace,
            "labels": labels,
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": labels,
            },
            "template": {
                "metadata": {
                    "labels": labels,
                },
                "spec": {
                    "containers": [
                        {
                            "name": deploy_name,
                            "image": image,
                            "imagePullPolicy": "IfNotPresent",
                        }
                    ]
                },
            },
            "revisionHistoryLimit": 10,
        },
    }
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    if resp.status_code != 200 and resp.status_code != 201:
        return -1, "디플로이먼트 배포 실패"
    return 1, "디플로이먼트 배포 성공"


def change_service_select_bg_label(
    cluster_url, cluster_token, service_name, namespace, bg_label
):
    url = cluster_url + "api/v1/namespaces/" + namespace + "/services/" + service_name
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return -1, "서비스 조회 실패"
    resp_json = resp.json()
    resp_json["spec"]["selector"]["bluegreen"] = bg_label

    url = cluster_url + "api/v1/namespaces/" + namespace + "/services/" + service_name
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.put(url, headers=headers, data=json.dumps(resp_json), verify=False)

    if resp.status_code != 200 and resp.status_code != 201:
        return -1, "서비스 변경 실패"
    return 1, "서비스 변경 성공"


def delete_deployment(cluster_url, cluster_token, deploy_name, namespace):
    url = (
        cluster_url
        + "apis/apps/v1/namespaces/"
        + namespace
        + "/deployments/"
        + deploy_name
    )
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.delete(url, headers=headers, verify=False)
    if resp.status_code != 200 and resp.status_code != 201:
        return -1, "디플로이먼트 삭제 실패"
    return 1, "디플로이먼트 삭제 성공"


if __name__ == "__main__":
    cluster_url = "https://192.168.50.21:6443"
    cluster_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InJ4Q05BRlZvbzJpeTlVSDFpaTVZdjN1UnRvc2xTZmliSlN4Vmp6cWhtYk0ifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tdjd6OHciLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjljZjU3NmZhLTYxZTgtNDlhMi05MDkzLTRiZjU1NmQ3MjI2NyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.aD7E_V3SBfiyKo8TbrCg8y8y4qfjxvk7eYF11ybApjuQMJBtrGNmPpz8R3rSC2ION5rKYQQLO7cmSlfUOrplBFFYfFWGTgdkeC3IKhpuTcI-YpCpQYz-ktafrbBLvZQkbkJ7_IBJ3bZHegehBHXrl2F2pgmu6ft1tjszFMctbFxgDlk4VrdG7BXHIPuWPY0ZXDfe0V5AuYq4D5WvNCjLZlPYDTifjM3bll5Tq79M6frti57My59dXfbQ-VUfgRHcJAA37ZLY3IDIpfRc5O2IjZg4XznceKPw0v2tEWVD1yez-lgMhqwxE-fIttLKsFZvO3RKfcN0R-JKctU3nJFVLQ"

    # 서비스 변경 TEST
    # namespace = "test1234"
    # service_name = "svc-nginx"
    # bg_label = "yellow"
    # ret_code, msg = change_service_select_label(
    #     cluster_url=cluster_url,
    #     cluster_token=cluster_token,
    #     namespace=namespace,
    #     service_name=service_name,
    #     bg_label=bg_label,
    # )
    # print(ret_code, msg)

    # 디플로이먼트 생성 TEST
    deploy_name = "test-blue"
    namespace = "test1234"
    image = "nginx:1.13"
    replicas = 1
    labels = {
        "app": "rollout-nginx",
        "app.kubernetes.io/instance": "testapp",
        "color": "blue",
        "canary": "canary",
    }

    if labels["color"] == "blue":
        deploy_name = deploy_name[:-4] + "green"
        labels["color"] = "green"

    elif labels["color"] == "green":
        deploy_name = deploy_name[:-5] + "blue"
        labels["color"] = "blue"
    print(
        create_deployment(
            cluster_url=cluster_url,
            cluster_token=cluster_token,
            deploy_name=deploy_name,
            namespace=namespace,
            image=image,
            replicas=replicas,
            labels=labels,
        )
    )
