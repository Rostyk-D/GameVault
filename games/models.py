from django.db import models


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

    description = models.TextField(
        blank=True,
    )

    cover = models.ImageField(
        upload_to="games/",
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
    )

    genres = models.ManyToManyField(
        Genre,
        related_name="games",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.title
