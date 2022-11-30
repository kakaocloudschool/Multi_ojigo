from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import ClusterForm, AppInfoForm
from .models import AppInfo

# Create your views here.
@login_required
def app_list(request):
    qs = AppInfo.objects.all()
    return render(request, "index.html", {"appinfo_list": qs})


@login_required
def new_cluster(request):
    if request.method == "POST":
        form = ClusterForm(request.POST, request.FILES)
        if form.is_valid():
            cluster = form.save(commit=False)
            file_content = cluster.kubeconfig.read().decode("utf-8")
            print(file_content)
            return redirect("/")
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
