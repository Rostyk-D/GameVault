from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    steam_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    reputation = models.PositiveIntegerField(
        default=0,
    )

    def __str__(self):
        return self.username
