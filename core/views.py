from django.db.models import Count, Q
from django.shortcuts import render

from users.models import User
from games.models import Game
from game_collections.models import GameCollection, CollectionVote


def home(request):
    featured_collections = (
        GameCollection.objects
        .filter(is_public=True)
        .with_statistics()
        .select_related("owner")
        .order_by(
            "-reputation",
            "-created_at",
        )[:3]
    )

    latest_collections = (
        GameCollection.objects
        .filter(is_public=True)
        .with_statistics()
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

    top_users = User.objects.order_by("-reputation")[:3]

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
