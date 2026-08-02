from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.core.paginator import Paginator
from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from games.models import Game

from game_collections.forms import (
    GameCollectionForm,
    SearchForm,
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
        queryset = (
            GameCollection.objects
            .filter(is_public=True)
            .annotate(
                likes=Count(
                    "collection_votes",
                    filter=Q(collection_votes__value=CollectionVote.LIKE),
                ),
                dislikes=Count(
                    "collection_votes",
                    filter=Q(collection_votes__value=CollectionVote.DISLIKE),
                ),
                games_count=Count("collection_games", distinct=True),
            )
            .annotate(reputation=F("likes") - F("dislikes"))
            .select_related(
                "owner"
            )
        )

        query = self.request.GET.get("query")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                |
                Q(description__icontains=query)
                |
                Q(owner__username__icontains=query)
            )

        return queryset.order_by(
            "-reputation",
            "-created_at",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = SearchForm(
            self.request.GET or None
        )

        return context


class GameCollectionDetailView(generic.DetailView):
    model = GameCollection
    template_name = "game_collections/collection_detail.html"
    context_object_name = "collection"

    def get_queryset(self):
        user = self.request.user

        votes_prefetch = Prefetch(
            "recommendation_votes",
            queryset=(
                RecommendationVote.objects.filter(
                    user=user,
                )
                if user.is_authenticated
                else RecommendationVote.objects.none()
            ),
            to_attr="user_votes",
        )

        return (
            GameCollection.objects
            .select_related(
                "owner",
            )
            .annotate(games_count=Count("collection_games", distinct=True))
            .prefetch_related(
                Prefetch(
                    "collection_games",
                    queryset=(
                        CollectionGame.objects
                        .select_related(
                            "game",
                        )
                        .prefetch_related(
                            votes_prefetch,
                        )
                        .annotate(
                            helpful_count=Count(
                                "recommendation_votes",
                                filter=Q(
                                    recommendation_votes__value=(
                                        RecommendationVote.HELPFUL
                                    )
                                ),
                                distinct=True,
                            ),
                            not_helpful_count=Count(
                                "recommendation_votes",
                                filter=Q(
                                    recommendation_votes__value=(
                                        RecommendationVote.NOT_HELPFUL
                                    )
                                ),
                                distinct=True,
                            ),
                            relevance_score=(
                                    Count(
                                        "recommendation_votes",
                                        filter=Q(
                                            recommendation_votes__value=(
                                                RecommendationVote.HELPFUL
                                            )
                                        ),
                                        distinct=True,
                                    )
                                    -
                                    Count(
                                        "recommendation_votes",
                                        filter=Q(
                                            recommendation_votes__value=(
                                                RecommendationVote.NOT_HELPFUL
                                            )
                                        ),
                                        distinct=True,
                                    )
                            ),
                        )
                        .order_by(
                            "-relevance_score",
                            "-created_at",
                        )
                    ),
                    to_attr="sorted_games",
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collection = self.object
        user = self.request.user

        if user.is_authenticated:
            context["user_vote"] = (
                CollectionVote.objects
                .filter(
                    user=user,
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

        games = self.object.sorted_games

        for item in games:
            if user.is_authenticated and item.user_votes:
                item.user_vote = item.user_votes[0].value
            else:
                item.user_vote = None

        query = self.request.GET.get(
            "query",
        )

        if query:
            games = [
                item
                for item in games
                if query.lower()
                in item.game.title.lower()
            ]

        paginator = Paginator(
            games,
            12
        )

        page_obj = paginator.get_page(
            self.request.GET.get("page")
        )

        context["collection_games"] = page_obj
        context["page_obj"] = page_obj
        context["is_paginated"] = page_obj.has_other_pages()

        context["search_form"] = SearchForm(
            self.request.GET or None,
        )

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

        CollectionGame.objects.bulk_create(
            [
                CollectionGame(collection=collection, game=game)
                for collection in collections
            ],
            ignore_conflicts=True,
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
