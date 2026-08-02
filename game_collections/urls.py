from django.urls import path, re_path

from game_collections import views


app_name = "game_collections"


urlpatterns = [

    # Collections

    path(
        "",
        views.GameCollectionListView.as_view(),
        name="list",
    ),

    path(
        "create/",
        views.GameCollectionCreateView.as_view(),
        name="create",
    ),

    path(
        "<int:pk>/",
        views.GameCollectionDetailView.as_view(),
        name="detail",
    ),

    path(
        "<int:pk>/update/",
        views.GameCollectionUpdateView.as_view(),
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.GameCollectionDeleteView.as_view(),
        name="delete",
    ),


    # Add game from game detail page

    path(
        "add-game/<int:game_id>/",
        views.AddGameFromGamePageView.as_view(),
        name="add-game-from-page",
    ),


    # Remove game

    path(
        "<int:pk>/games/<int:game_id>/remove/",
        views.RemoveGameFromCollectionView.as_view(),
        name="remove-game",
    ),


    # Votes

    re_path(
        r"^(?P<pk>[0-9]+)/vote/(?P<value>-?[0-9]+)/$",
        views.CollectionVoteView.as_view(),
        name="vote",
    ),

    re_path(
        r"^game/(?P<pk>[0-9]+)/recommendation-vote/(?P<value>-?[0-9]+)/$",
        views.RecommendationVoteView.as_view(),
        name="recommendation-vote",
    ),
]
