from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from games.models import Game

from game_collections.forms import (
    GameCollectionForm,
    GameSearchForm,
)

from game_collections.models import (
    GameCollection,
    CollectionGame,
    RecommendationVote,
    CollectionVote,
)


class GameCollectionListView(generic.ListView):
    model = GameCollection
    template_name = "game_collections/collection_list.html"
    context_object_name = "collections"
    paginate_by = 12

    def get_queryset(self):
        return (
            GameCollection.objects
            .filter(is_public=True)
            .annotate(
                reputation=(
                        Count(
                            "collection_votes",
                            filter=Q(
                                collection_votes__value=1
                            )
                        )
                        -
                        Count(
                            "collection_votes",
                            filter=Q(
                                collection_votes__value=-1
                            )
                        )
                )
            )
            .select_related(
                "owner"
            )
            .order_by(
                "-reputation",
                "-created_at",
            )
        )


class GameCollectionDetailView(generic.DetailView):
    model = GameCollection
    template_name = "game_collections/collection_detail.html"
    context_object_name = "collection"

    def get_queryset(self):
        return (
            GameCollection.objects
            .select_related(
                "owner"
            )
            .prefetch_related(
                "collection_games__game"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collection = self.object

        if self.request.user.is_authenticated:
            context["user_vote"] = (
                CollectionVote.objects
                .filter(
                    user=self.request.user,
                    collection=collection,
                )
                .values_list(
                    "value",
                    flat=True,
                )
                .first()
            )
        else:
            context["user_vote"] = None

        context["search_form"] = GameSearchForm(
            self.request.GET or None
        )

        games = (
            collection.collection_games
            .select_related(
                "game",
            )
            .annotate(
                helpful_score=(
                        Count(
                            "recommendation_votes",
                            filter=Q(
                                recommendation_votes__value=1
                            )
                        )
                        -
                        Count(
                            "recommendation_votes",
                            filter=Q(
                                recommendation_votes__value=-1
                            )
                        )
                )
            )
            .order_by(
                "-helpful_score",
                "-created_at",
            )
        )

        query = self.request.GET.get(
            "query"
        )

        if query:
            games = games.filter(
                game__title__icontains=query
            )

        context["collection_games"] = games

        return context


class GameCollectionCreateView(
    LoginRequiredMixin,
    generic.CreateView
):
    model = GameCollection
    form_class = GameCollectionForm
    template_name = "game_collections/collection_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "game_collections:detail",
            kwargs={
                "pk": self.object.pk
            }
        )


class GameCollectionUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.UpdateView
):
    model = GameCollection
    form_class = GameCollectionForm
    template_name = "game_collections/collection_form.html"

    def test_func(self):
        return (
                self.request.user ==
                self.get_object().owner
        )

    def get_success_url(self):
        return reverse_lazy(
            "game_collections:detail",
            kwargs={
                "pk": self.object.pk
            }
        )


class GameCollectionDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.DeleteView
):
    model = GameCollection
    template_name = "game_collections/collection_confirm_delete.html"

    def test_func(self):
        return (
                self.request.user ==
                self.get_object().owner
        )

    def get_success_url(self):
        return reverse_lazy(
            "game_collections:list"
        )


class AddGameFromGamePageView(
    LoginRequiredMixin,
    generic.View,
):
    def post(
        self,
        request,
        game_id,
    ):

        game = get_object_or_404(
            Game,
            pk=game_id,
        )

        collection_ids = request.POST.getlist(
            "collections"
        )

        collections = GameCollection.objects.filter(
            id__in=collection_ids,
            owner=request.user,
        )

        for collection in collections:

            CollectionGame.objects.get_or_create(
                collection=collection,
                game=game,
            )

        return redirect(
            "games:game-detail",
            pk=game.pk,
        )


class RemoveGameFromCollectionView(
    LoginRequiredMixin,
    generic.View,
):

    def post(
            self,
            request,
            pk,
            game_id,
    ):
        collection = get_object_or_404(
            GameCollection,
            pk=pk,
            owner=request.user,
        )

        CollectionGame.objects.filter(
            collection=collection,
            game_id=game_id,
        ).delete()

        return redirect(
            "game_collections:detail",
            pk=collection.pk,
        )


class RecommendationVoteView(
    LoginRequiredMixin,
    generic.View,
):

    def post(
            self,
            request,
            pk,
            value,
    ):
        collection_game = get_object_or_404(
            CollectionGame,
            pk=pk,
        )

        vote, created = RecommendationVote.objects.get_or_create(
            user=request.user,
            collection_game=collection_game,
            defaults={
                "value": value,
            }
        )

        if not created:
            if vote.value == value:
                vote.delete()
            else:
                vote.value = value
                vote.save()

        return redirect(
            "game_collections:detail",
            pk=collection_game.collection.pk,
        )


class CollectionVoteView(
    LoginRequiredMixin,
    generic.View,
):

    def post(
            self,
            request,
            pk,
            value,
    ):
        collection = get_object_or_404(
            GameCollection,
            pk=pk,
        )

        vote, created = CollectionVote.objects.get_or_create(
            user=request.user,
            collection=collection,
            defaults={
                "value": value,
            }
        )

        if not created:
            if vote.value == value:
                vote.delete()
            else:
                vote.value = value
                vote.save()

        return redirect(
            "game_collections:detail",
            pk=pk,
        )
