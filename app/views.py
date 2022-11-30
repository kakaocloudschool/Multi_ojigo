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
def cluster_new(request):
    if request.method == "POST":
        form = ClusterForm(request.POST, request.FILES)
        if form.is_valid():
            cluster = form.save(commit=True)
            return redirect("/")
    else:
        form = ClusterForm()

    return render(request, "app/cluster_add.html", {"form": form})


@login_required
def cluster_new(request):
    if request.method == "POST":
        form = AppInfoForm(request.POST, request.FILES)
        if form.is_valid():
            cluster = form.save(commit=True)
            return redirect("/")
    else:
        form = AppInfoForm()

    return render(request, "app/cluster_add.html", {"form": form})
