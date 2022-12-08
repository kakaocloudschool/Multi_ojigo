from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import auth
from .forms import SignupForm


@login_required
def signup_view(request):
    # if request.user.group != "admin":
    #    return redirect("app_list")
    if request.method == "POST":
        print(request.method)
        form = SignupForm(request.POST)
        if form.is_valid():
            # print("1")
            user = form.save()
            auth.login(request, user)
            return redirect("/")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})
