from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import AppInfo

# Create your views here.
@login_required
def app_list(request):
    qs = AppInfo.objects.all()
    return render(request, "index.html", {"appinfo_list": qs})
