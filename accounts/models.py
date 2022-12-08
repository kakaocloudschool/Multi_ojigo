from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    MY_USERS = (  # 각 튜플의 첫 번째 요소는 DB에 저장할 실제 값이고, 두 번째 요소는 display 용 이름이다.
        ("Manager", "매니저"),
        ("User", "유저"),
    )

    group = models.CharField(max_length=100)
    privilege = models.CharField(
        max_length=20, choices=MY_USERS, default="User"
    )
