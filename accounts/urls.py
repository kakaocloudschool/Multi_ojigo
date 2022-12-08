from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from .views import signup_view

app_name = "accounts"

urlpatterns = [
    path(
        "login/", LoginView.as_view(template_name="accounts/login.html"), name="login"
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('signup/', signup_view, name='signup'),
]
