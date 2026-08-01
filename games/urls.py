from django.urls import path, re_path

from games.views import (
    GameListView,
    GameDetailView,
    GameCommentCreateUpdateView,
    CommentVoteView,
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
    re_path(
        r"^comment/(?P<pk>[0-9]+)/(?P<value>-?[0-9]+)/$",
        CommentVoteView.as_view(),
        name="comment-vote",
    ),
]
