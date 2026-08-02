from django.db.models import Count, F, Q
from django.shortcuts import render

from users.models import User
from games.models import Game
from game_collections.models import GameCollection


def home(request):
    featured_collections = (
        GameCollection.objects
        .filter(is_public=True)
        .annotate(
            likes=Count(
                "collection_votes",
                filter=Q(
                    collection_votes__value=1
                ),
                distinct=True,
            ),
            dislikes=Count(
                "collection_votes",
                filter=Q(
                    collection_votes__value=-1
                ),
                distinct=True,
            ),
            games_count=Count("collection_games", distinct=True),
        )
        .annotate(reputation=F("likes") - F("dislikes"))
        .select_related("owner")
        .order_by(
            "-reputation",
            "-created_at",
        )[:3]
    )

    latest_collections = (
        GameCollection.objects
        .filter(is_public=True)
        .annotate(
            games_count=Count("collection_games", distinct=True),
        )
        .select_related("owner")
        .order_by(
            "-created_at"
        )[:3]
    )

    most_used_games = (
        Game.objects
        .annotate(
            collection_count=Count(
                "collection_games",
                distinct=True,
            )
        )
        .order_by(
            "-collection_count"
        )[:3]
    )

    top_users = (
        User.objects
        .annotate(
            best_collection_rating=Count(
                "game_collections__collection_votes",
                filter=Q(
                    game_collections__collection_votes__value=1
                ),
                distinct=True,
            )
            -
            Count(
                "game_collections__collection_votes",
                filter=Q(
                    game_collections__collection_votes__value=-1
                ),
                distinct=True,
            )
        )
        .order_by(
            "-best_collection_rating"
        )[:3]
    )

    context = {
        "featured_collections": featured_collections,
        "latest_collections": latest_collections,
        "most_used_games": most_used_games,
        "top_users": top_users,
    }

    return render(
        request,
        "core/home.html",
        context,
    )
