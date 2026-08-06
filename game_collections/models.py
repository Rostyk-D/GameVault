from django.conf import settings
from django.db import models

from core.slugs import create_unique_slug
from games.models import Game


class GameCollectionQuerySet(models.QuerySet):
    def with_statistics(self):
        return self.annotate(
            likes=models.Count(
                "collection_votes",
                filter=models.Q(collection_votes__value=CollectionVote.LIKE),
                distinct=True,
            ),
            dislikes=models.Count(
                "collection_votes",
                filter=models.Q(collection_votes__value=CollectionVote.DISLIKE),
                distinct=True,
            ),
            games_count=models.Count("collection_games", distinct=True),
        ).annotate(reputation=models.F("likes") - models.F("dislikes"))


class GameCollection(models.Model):
    objects = GameCollectionQuerySet.as_manager()

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_collections",
    )

    title = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
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
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_unique_slug(
                self,
                self.title,
                fallback="collection",
                reserved_slugs=("create",),
            )

        super().save(*args, **kwargs)


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

    position = models.PositiveIntegerField(
        default=0,
    )

    author_rating = models.PositiveSmallIntegerField(
        default=5,
        help_text="Author rating of this game in collection (1-5)",
    )

    recommendation = models.TextField(
        blank=True,
        help_text="Why should I play this game?",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "position",
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "collection",
                    "game",
                ],
                name="unique_game_in_collection",
            )
        ]

    def __str__(self):
        return (
            f"{self.collection.title} - "
            f"{self.game.title}"
        )


class CollectionVote(models.Model):
    LIKE = 1
    DISLIKE = -1

    VOTE_CHOICES = (
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collection_votes",
    )

    collection = models.ForeignKey(
        GameCollection,
        on_delete=models.CASCADE,
        related_name="collection_votes",
    )

    value = models.SmallIntegerField(
        choices=VOTE_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "collection",
                ],
                name="unique_collection_vote",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.collection.title} - "
            f"{self.value}"
        )


class RecommendationVote(models.Model):
    HELPFUL = 1
    NOT_HELPFUL = -1

    VOTE_CHOICES = (
        (HELPFUL, "Helpful"),
        (NOT_HELPFUL, "Not helpful"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendation_votes",
    )

    collection_game = models.ForeignKey(
        CollectionGame,
        on_delete=models.CASCADE,
        related_name="recommendation_votes",
    )

    value = models.SmallIntegerField(
        choices=VOTE_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "collection_game",
                ],
                name="unique_recommendation_vote",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.collection_game.game.title} - "
            f"{self.value}"
        )
