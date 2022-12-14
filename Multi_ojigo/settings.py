"""
Django settings for Multi_ojigo project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import json
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy
import pymysql
from django.contrib.messages import constants as messages_constants

MESSAGE_LEVEL = messages_constants.INFO  # 디폴트 설정

MESSAGE_LEVEL = messages_constants.DEBUG

MESSAGE_TAGS = {
    messages_constants.DEBUG: "secondary",
    messages_constants.ERROR: "danger",
}


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOGIN_REDIRECT_URL = "/"
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

secret_file = os.path.join(BASE_DIR, "secrets.json")

with open(secret_file) as f:
    secrets = json.loads(f.read())


def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_secret("SECRET_KEY")
DEBUG = get_secret("DEBUG")
ARGOCD_URL = get_secret("ARGOCD_URL")
ARGOCD_USERNAME = get_secret("ARGOCD_USERNAME")
ARGO_PASSWORD = get_secret("ARGO_PASSWORD")
GITHUB_TOKEN = get_secret("GITHUB_TOKEN")


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "192.168.0.0",
]

# APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
# APSCHEDULER_RUN_NOW_TIMEOUT = 25

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd Party APP
    "bootstrap4",
    "django_bootstrap5",
    # local apps
    "accounts",
    "app",
    "django_apscheduler",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Multi_ojigo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Multi_ojigo.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

pymysql.install_as_MySQLdb()
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    # DATABASES = {
    #     "default": {
    #         "ENGINE": "django.db.backends.mysql",
    #         "NAME": "argocd",
    #         "USER": "root",
    #         "PASSWORD": "test123",
    #         "HOST": "127.0.0.1",
    #         "PORT": "3306",
    #         "OPTIONS": {"init_command": 'SET sql_mode="STRICT_TRANS_TABLES"'},
    #     }
    # }

# else:
#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.mysql",
#             "NAME": "argocd",
#             "USER": "root",
#             "PASSWORD": "test123",
#             "HOST": "192.168.50.106",
#             "PORT": "3306",
#             "OPTIONS": {"init_command": 'SET sql_mode="STRICT_TRANS_TABLES"'},
#         }
#     }


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "Multi_ojigo", "static"),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.CustomUser"
