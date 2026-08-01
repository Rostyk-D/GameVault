from django.db.models import Q
from django.views import generic

from games.forms import GameSearchForm
from games.models import Game


class GameListView(generic.ListView):
    model = Game
    template_name = "games/game_list.html"
    context_object_name = "games"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Game.objects
            .select_related("developer")
            .prefetch_related("genres")
            .order_by("title")
        )

        query = self.request.GET.get("q")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(developer__name__icontains=query)
                | Q(genres__name__icontains=query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = GameSearchForm(
            self.request.GET or None
        )

        return context


class GameDetailView(generic.DetailView):
    model = Game
    template_name = "games/game_detail.html"
    context_object_name = "game"
