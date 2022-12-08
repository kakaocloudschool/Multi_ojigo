from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    group = models.CharField(max_length=100)
    privilege = models.CharField(max_length=100)
