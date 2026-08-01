from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Developer(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )

    def __str__(self):
        return self.name


class Game(models.Model):
    title = models.CharField(
        max_length=150,
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    cover = models.URLField(
        blank=True,
        null=True,
    )

    steam_appid = models.PositiveIntegerField(
        unique=True,
        blank=True,
        null=True,
    )

    release_date = models.DateField(
        blank=True,
        null=True,
    )

    developer = models.ForeignKey(
        Developer,
        on_delete=models.CASCADE,
        related_name="games",
        null=True,
    )

    genres = models.ManyToManyField(
        Genre,
        related_name="games",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Game.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserGame(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="steam_library"
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="players"
    )

    playtime_forever = models.PositiveIntegerField(
        default=0
    )

    last_played = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = (
            "user",
            "game",
        )


class GameComment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_comments",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    text = models.TextField(
        max_length=1000,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "game",
                ],
                name="unique_user_game_comment",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.game.title}"

class CommentVote(models.Model):
    LIKE = 1
    DISLIKE = -1

    VOTE_CHOICES = (
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_votes",
    )

    comment = models.ForeignKey(
        GameComment,
        on_delete=models.CASCADE,
        related_name="votes",
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
                    "comment",
                ],
                name="unique_comment_vote",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.comment} - {self.value}"
