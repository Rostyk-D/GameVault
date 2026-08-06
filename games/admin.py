from django.contrib import admin

from games.models import (
    Game,
    Genre,
    Developer,
    GameComment,
    CommentVote,
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
        "developer__name",
    )

    list_filter = (
        "developer",
        "genres",
        "release_date",
    )

    filter_horizontal = (
        "genres",
    )


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(GameComment)
class GameCommentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "game",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "game__title",
        "text",
    )

    list_filter = (
        "game",
        "updated_at",
    )


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "comment",
        "value",
        "created_at",
    )

    search_fields = (
        "user__username",
        "comment__text",
        "comment__game__title",
    )

    list_filter = (
        "value",
        "created_at",
    )
