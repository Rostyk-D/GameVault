from django.urls import path

from games.views import (
    GameListView,
    GameDetailView,
    GameCommentCreateUpdateView,
)

app_name = "games"

urlpatterns = [
    path(
        "",
        GameListView.as_view(),
        name="game-list",
    ),

    path(
        "<int:pk>/",
        GameDetailView.as_view(),
        name="game-detail",
    ),
    path(
        "<int:pk>/comment/",
        GameCommentCreateUpdateView.as_view(),
        name="game-comment"
    ),
]
