from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.views import generic

from games.forms import GameSearchForm, GameCommentForm
from games.models import Game, GameComment


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        if user.is_authenticated:
            comment = GameComment.objects.filter(
                game=self.object,
                user=user,
            ).first()

            context["user_comment"] = comment
            context["comment_form"] = GameCommentForm(
                instance=comment
            )
        else:
            context["user_comment"] = None
            context["comment_form"] = None

        return context


class GameCommentCreateUpdateView(LoginRequiredMixin, generic.View):

    def post(self, request, pk):
        game = Game.objects.get(pk=pk)

        comment = GameComment.objects.filter(
            game=game,
            user=request.user,
        ).first()

        form = GameCommentForm(
            request.POST,
            instance=comment,
        )

        if form.is_valid():
            comment = form.save(commit=False)
            comment.game = game
            comment.user = request.user
            comment.save()

        return redirect(
            "games:game-detail",
            pk=pk,
        )
