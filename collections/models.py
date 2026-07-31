from django.conf import settings
from django.db import models

from games.models import Game


class GameCollection(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections",
    )

    title = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    is_public = models.BooleanField(
        default=True,
    )

    views = models.PositiveIntegerField(
        default=0,
    )

    likes = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    games = models.ManyToManyField(
        Game,
        through="CollectionGame",
        related_name="collections",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class CollectionGame(models.Model):
    collection = models.ForeignKey(
        GameCollection,
        on_delete=models.CASCADE,
        related_name="collection_games",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="collection_games",
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    rating = models.PositiveSmallIntegerField(
        default=5,
    )

    recommendation = models.TextField(
        help_text="Why should I play this?",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["collection", "game"],
                name="unique_game_in_collection",
            )
        ]

    def __str__(self):
        return f"{self.collection} - {self.game}"


class RecommendationVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendation_votes",
    )

    collection_game = models.ForeignKey(
        CollectionGame,
        on_delete=models.CASCADE,
        related_name="votes",
    )

    is_helpful = models.BooleanField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "collection_game"],
                name="unique_recommendation_vote",
            )
        ]
