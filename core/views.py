from django.shortcuts import render
from django.db.models import Count

from game_collections.models import GameCollection
from games.models import Game
from users.models import User


def home(request):
    context = {
        "popular_collections": GameCollection.objects.filter(
            is_public=True
        ).order_by("-likes")[:6],

        "latest_collections": GameCollection.objects.filter(
            is_public=True
        ).order_by("-created_at")[:6],

        "most_used_games": Game.objects.annotate(
            collection_count=Count("game_collections")
        ).order_by("-collection_count")[:6],

        "top_users": User.objects.order_by(
            "-reputation"
        )[:5],
    }

    return render(
        request,
        "core/home.html",
        context
    )
