from django.contrib.auth.models import AbstractUser
from django.db import models

from games.models import Game


class User(AbstractUser):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

    GENDER_CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
        (OTHER, "Other"),
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    favorite_game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="favorite_by_users",
    )

    steam_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )

    reputation = models.PositiveIntegerField(
        default=0,
    )
