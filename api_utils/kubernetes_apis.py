import requests
from requests.structures import CaseInsensitiveDict
import json

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


def parsing_kube_confing(file_content):
    # with open(file_path) as f:
    server = "-1"
    ca_data = "-1"
    for line in file_content.split("\n"):
        line_subject = line.split(":")[0].strip()
        if line_subject == "certificate-authority-data":
            ca_data = line.split(":")[1].strip()
        elif line_subject == "server":
            server = "".join(line.strip().split("server:")[1]).strip() + "/"
    return server, ca_data


def is_have_namespace(cluster_url: str, cluster_token: str, namespace: str) -> bool:
    url = cluster_url + "api/v1/namespaces/" + namespace
    print(url)
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    resp = requests.get(url, headers=headers, verify=False)
    print(resp.text)
    if resp.json()["kind"] == "Namespace":
        return True
    elif resp.json()["code"] == 404:
        return False
    else:
        print("error")
        return True


def create_namespace_in_cluster(cluster_url: str, cluster_token: str, namespace: str):
    url = cluster_url + "api/v1/namespaces/"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {cluster_token}"
    data = {"kind": "Namespace", "apiVersion": "v1", "metadata": {"name": namespace}}
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    print(resp.text)
