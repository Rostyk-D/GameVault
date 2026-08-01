from django.urls import path

from games.views import (
    GameListView,
    GameDetailView,
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
]
