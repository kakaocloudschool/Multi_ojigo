import requests
from requests.structures import CaseInsensitiveDict
import base64
import json
from django.conf import settings

GITHUB_TOKEN = getattr(settings, "GITHUB_TOKEN", None)


def deploy_done(
    git_repository,
    target_branch,
    repository_path,
    deployment,
    bef_bluegreen,
    bef_canary,
    chg_bluegreen,
    chg_canary,
):
    basic_url = "https://raw.githubusercontent.com/"
    basic_api_url = "https://api.github.com/repos/"
    github_token = GITHUB_TOKEN

    git_repo = git_repository.split("/")[-2:]
    if len(git_repo[1]) > 4 and git_repo[1][-4:] == ".git":
        git_repo[1] = git_repo[1][:-4]

    bef_url = (
        basic_url
        + "/".join(git_repo)
        + "/"
        + target_branch
        + "/"
        + repository_path
        + "/deploy/"
        + bef_bluegreen
        + "/"
        + bef_canary
        + "/kustomization.yaml"
    )
    bef_upload_url = (
        basic_api_url
        + "/".join(git_repo)
        + "/contents/"
        + repository_path
        + "/deploy/"
        + bef_bluegreen
        + "/"
        + bef_canary
        + "/kustomization.yaml"
    )
    tar_url = (
        basic_url
        + "/".join(git_repo)
        + "/"
        + target_branch
        + "/"
        + repository_path
        + "/deploy/"
        + chg_bluegreen
        + "/"
        + chg_canary
        + "/kustomization.yaml"
    )
    chg_upload_url = (
        basic_api_url
        + "/".join(git_repo)
        + "/contents/"
        + repository_path
        + "/deploy/"
        + chg_bluegreen
        + "/"
        + chg_canary
        + "/kustomization.yaml"
    )

    resp = requests.get(bef_url)
    target = "-".join(deployment.split("-")[1:-2])

    target_text = []
    target_path = ""
    for text in resp.text.split("\n"):
        if text.split("/")[-1] == target:
            target_path = text
        else:
            target_text.append(text)

    print("target_path :", target_path)
    before_text = "\n".join(target_text)
    resp = requests.get(tar_url)
    target_text = []

    count = 0
    for text in resp.text.split("\n"):
        if count == 2:
            target_text.append(target_path)
        target_text.append(text)
        count += 1

    chg_text = "\n".join(target_text)
    # # test code
    # bef_upload_url = basic_api_url + "/".join(git_repo) + "/contents/" + "test.txt"
    # print(before_text)
    # print(chg_text)

    result_code, msg = github_edit_file(
        github_url=bef_upload_url, github_token=github_token, text_content=before_text
    )
    if result_code == -1:
        return -1, "GIT 저장소 변경 실패"

    result_code, msg = github_edit_file(
        github_url=chg_upload_url, github_token=github_token, text_content=chg_text
    )
    if result_code == -1:
        return -1, "GIT 저장소 변경 실패"

    return 1, "GIT 변경 성공"


def github_edit_file(github_url, github_token, text_content):
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {github_token}"
    resp = requests.get(github_url, headers=headers, verify=False)

    if resp.status_code != 200 and resp.status_code != 201:
        return -1, "깃허브 연동 실패"
    bef_upload_sha = resp.json()["sha"]

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {github_token}"
    data = {
        "message": "Multi Deploy-Go auto-commit",
        "content": base64.b64encode(text_content.encode("UTF-8")).decode("ascii"),
        "sha": bef_upload_sha,
    }
    resp = requests.put(
        github_url, headers=headers, data=json.dumps(data), verify=False
    )

    if resp.status_code != 200 and resp.status_code != 201:
        return -1, "깃허브 연동 실패"
    return 1, "깃허브 변경 완료"


if __name__ == "__main__":
    git_repository = "https://github.com/kakaocloudschool/kustomize-test.git"
    target_branch = "main"
    repository_path = "overlays/prod"
    deployment = "deploy-httpd-stable-s"
    bef_bluegreen = "blue"
    bef_canary = "stable"
    chg_bluegreen = "blue"
    chg_canary = "canary"
    deploy_done(
        git_repository=git_repository,
        target_branch=target_branch,
        repository_path=repository_path,
        deployment=deployment,
        bef_bluegreen=bef_bluegreen,
        bef_canary=bef_canary,
        chg_bluegreen=chg_bluegreen,
        chg_canary=chg_canary,
    )
