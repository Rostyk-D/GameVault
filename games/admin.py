from django.contrib import admin

from games.models import (
    Game,
    Genre,
    Developer,
)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "developer",
        "release_date",
    )

    search_fields = (
        "title",
    )

    list_filter = (
        "developer",
        "genres",
    )


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    search_fields = (
        "name",
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = (
        "name",
    )
