from django.shortcuts import render
from django.db.models import Count

from game_collections.models import GameCollection
from games.models import Game
from users.models import User


def home(request):
    context = {
        "popular_collections": GameCollection.objects.filter(
            is_public=True
        ).order_by("-likes")[:3],

        "latest_collections": GameCollection.objects.filter(
            is_public=True
        ).order_by("-created_at")[:3],

        "most_used_games": Game.objects.annotate(
            collection_count=Count("game_collections")
        ).order_by("-collection_count")[:3],

        "top_users": User.objects.order_by(
            "-reputation"
        )[:3],
    }

    return render(
        request,
        "core/home.html",
        context
    )
