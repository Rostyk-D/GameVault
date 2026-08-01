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

    PUBLIC = "public"
    PRIVATE = "private"

    STEAM_PROFILE_CHOICES = (
        (PUBLIC, "Public"),
        (PRIVATE, "Private"),
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

    steam_library_status = models.CharField(
        max_length=10,
        choices=STEAM_PROFILE_CHOICES,
        default=PRIVATE,
    )

    steam_sync_status = models.CharField(
        max_length=20,
        default="not_synced",
    )

    steam_last_sync = models.DateTimeField(
        null=True,
        blank=True,
    )

    steam_last_update_request = models.DateTimeField(
        null=True,
        blank=True,
    )

    steam_sync_progress = models.PositiveIntegerField(
        default=0
    )

    reputation = models.PositiveIntegerField(
        default=0,
    )
