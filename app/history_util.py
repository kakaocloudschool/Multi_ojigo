from app.models import AppDeployRevision, AppDeployHistory


def append_appdeployhistory(pk):
    app_revision = AppDeployRevision.objects.get(pk=pk)
    appdeployhistory = AppDeployHistory()
    appdeployhistory.AppDeployRevision_id = str(pk)
    appdeployhistory.app_name = str(app_revision.app_name)
    appdeployhistory.deploy_type = app_revision.deploy_type
    appdeployhistory.cluster_name = app_revision.cluster_name
    appdeployhistory.cluster_url = app_revision.cluster_url
    appdeployhistory.namespace = app_revision.namespace
    appdeployhistory.deployment = app_revision.deployment
    appdeployhistory.new_deployment = app_revision.new_deployment
    appdeployhistory.container = app_revision.container
    appdeployhistory.tag = app_revision.tag
    appdeployhistory.before_color = app_revision.before_color
    appdeployhistory.change_color = app_revision.change_color
    appdeployhistory.target_service = app_revision.target_service
    appdeployhistory.step = app_revision.step
    appdeployhistory.manager_user = app_revision.insert_user
    appdeployhistory.canary_sterategy = app_revision.canary_sterategy
    appdeployhistory.insert_user = app_revision.update_user
    appdeployhistory.save()
