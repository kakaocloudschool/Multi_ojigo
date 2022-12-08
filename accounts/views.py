from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import auth
from .forms import SignupForm

def signup_view(request):
  if request.method == 'POST':
    form = SignupForm(request.POST)
    if form.is_valid():
      user = form.save()
      auth.login(request, user)
      return redirect('login')
    return redirect('login')

  else:
    form = SignupForm()
    return render(request, 'accounts/signup.html', {'form' : form})