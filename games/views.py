from django.views import generic

from games.models import Game


class GameListView(generic.ListView):
    model = Game
    template_name = "games/game_list.html"
    context_object_name = "games"
    paginate_by = 12

    def get_queryset(self):
        return (
            Game.objects
            .select_related("developer")
            .prefetch_related("genres")
            .order_by("title")
        )


class GameDetailView(generic.DetailView):
    model = Game
    template_name = "games/game_detail.html"
    context_object_name = "game"
