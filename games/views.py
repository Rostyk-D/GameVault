from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Value,
    When,
)
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from games.forms import GameSearchForm, GameCommentForm
from games.models import Game, GameComment, CommentVote
from game_collections.models import GameCollection


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
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Game.objects
            .select_related("developer")
            .prefetch_related("genres")
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated:
            return redirect("login")

        comment = GameComment.objects.filter(
            game=self.object,
            user=request.user
        ).first()

        form = GameCommentForm(
            request.POST,
            instance=comment
        )

        if form.is_valid():
            comment = form.save(commit=False)
            comment.game = self.object
            comment.user = request.user
            comment.save()

        return redirect(
            "games:game-detail",
            slug=self.object.slug,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        if user.is_authenticated:
            user_comment = GameComment.objects.filter(
                game=self.object,
                user=user
            ).first()

            context["user_comment"] = user_comment
            context["comment_form"] = GameCommentForm(
                instance=user_comment
            )

            collections = (
                GameCollection.objects
                .filter(owner=user)
                .annotate(
                    has_game=Exists(
                        GameCollection.games.through.objects.filter(
                            collection_id=OuterRef("pk"),
                            game_id=self.object.pk,
                        )
                    )
                )
            )

            context["user_collections"] = collections

        else:
            context["user_comment"] = None
            context["comment_form"] = None
            context["user_collections"] = []

        comments = (
            self.object.comments
            .select_related("user")
            .annotate(
                likes_count=Count(
                    "votes",
                    filter=Q(
                        votes__value=CommentVote.LIKE
                    )
                ),
                dislikes_count=Count(
                    "votes",
                    filter=Q(
                        votes__value=CommentVote.DISLIKE
                    )
                )
            )
            .annotate(
                rating=F("likes_count") - F("dislikes_count")
            )
        )

        if user.is_authenticated:
            comments = comments.annotate(
                is_owner=Case(
                    When(
                        user=user,
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by(
                "-is_owner",
                "-rating",
                "-updated_at"
            )
        else:
            comments = comments.order_by(
                "-rating",
                "-updated_at"
            )

        if user.is_authenticated:
            comments = comments.prefetch_related(
                Prefetch(
                    "votes",
                    queryset=CommentVote.objects.filter(user=user),
                    to_attr="user_votes",
                )
            )

        paginator = Paginator(
            comments,
            10
        )

        page_number = self.request.GET.get(
            "page"
        )

        page_obj = paginator.get_page(
            page_number
        )

        if user.is_authenticated:
            for comment in page_obj:
                comment.user_vote = (
                    comment.user_votes[0].value
                    if comment.user_votes
                    else 0
                )

        context["comments"] = page_obj
        context["page_obj"] = page_obj
        context["is_paginated"] = page_obj.has_other_pages()

        return context


class GameCommentCreateUpdateView(
    LoginRequiredMixin,
    generic.UpdateView
):
    model = GameComment
    form_class = GameCommentForm

    def get_object(self):
        comment, created = GameComment.objects.get_or_create(
            game_id=self.kwargs["pk"],
            user=self.request.user,
            defaults={
                "text": ""
            }
        )

        return comment

    def form_valid(self, form):
        form.instance.game_id = self.kwargs["pk"]
        form.instance.user = self.request.user

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "games:game-detail",
            kwargs={
                "slug": self.object.game.slug
            }
        )


class CommentVoteView(
    LoginRequiredMixin,
    generic.View
):

    def post(
        self,
        request,
        pk,
        value
    ):
        comment = get_object_or_404(
            GameComment,
            pk=pk
        )

        vote, created = CommentVote.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={
                "value": value
            }
        )

        if not created:
            if vote.value == value:
                vote.delete()
            else:
                vote.value = value
                vote.save()

        return redirect(
            "games:game-detail",
            slug=comment.game.slug
        )
