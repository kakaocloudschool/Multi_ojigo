from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SignupForm(UserCreationForm):
  class Meta:
    model = CustomUser
    fields = ['username', 'password1', 'password2', 'group', 'privilege']
    widgets = {
      'privilege': forms.Select
    }
