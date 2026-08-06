import asyncio
import threading
from datetime import timedelta

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth import views, logout
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.core.paginator import Paginator

from game_collections.models import (
    GameCollection,
    CollectionVote
)
from games.models import Game, UserGame
from games.services import SteamService
from users.forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    SteamLibrarySearchForm,
)
from users.models import User


def sync_library_background(user_id):
    user = User.objects.get(
        id=user_id
    )
    user.steam_sync_status = "syncing"
    user.save(
        update_fields=[
            "steam_sync_status"
        ]
    )
    try:
        asyncio.run(
            SteamService.sync_library(
                user
            )
        )
    except Exception:
        user.steam_sync_status = "error"
        user.save(
            update_fields=[
                "steam_sync_status"
            ]
        )


class RegisterView(generic.CreateView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy(
        "users:login"
    )


class LoginView(views.LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"


class GameAutocomplete(
    autocomplete.Select2QuerySetView
):
    def get_queryset(self):
        qs = Game.objects.all()

        if self.q:
            qs = qs.filter(
                title__icontains=self.q
            )

        return qs.order_by("title")


class ProfileDetailView(
    LoginRequiredMixin,
    generic.DetailView
):
    model = User
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def get_object(self):
        return get_object_or_404(
            User.objects.select_related("favorite_game").annotate(
                reputation_score=(
                        Count(
                            "game_collections__collection_votes",
                            filter=Q(
                                game_collections__collection_votes__value=(
                                    CollectionVote.LIKE
                                ),
                            ),
                            distinct=True,
                        )
                        -
                        Count(
                            "game_collections__collection_votes",
                            filter=Q(
                                game_collections__collection_votes__value=(
                                    CollectionVote.DISLIKE
                                ),
                            ),
                            distinct=True,
                        )
                )
            ),
            pk=self.kwargs["pk"],
        )

    def get_context_data(
            self,
            **kwargs
    ):
        context = super().get_context_data(
            **kwargs
        )

        if self.request.user == self.object:
            context["form"] = UserProfileForm(
                instance=self.object
            )

        steam_library = (
            UserGame.objects
            .filter(
                user=self.object
            )
            .select_related(
                "game"
            )
            .order_by(
                "-playtime_forever"
            )
        )

        query = self.request.GET.get("query")

        if query:
            steam_library = steam_library.filter(
                game__title__icontains=query
            )

        context["steam_search_form"] = SteamLibrarySearchForm(
            self.request.GET or None
        )

        collections = (
            GameCollection.objects
            .filter(owner=self.object)
            .with_statistics()
            .order_by("-created_at")
        )

        context["collections"] = collections

        paginator = Paginator(
            steam_library,
            12
        )

        page_obj = paginator.get_page(
            self.request.GET.get("page")
        )

        context["steam_library_page"] = page_obj
        context["page_obj"] = page_obj
        context["is_paginated"] = page_obj.has_other_pages()

        return context


class ProfileUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.UpdateView
):
    model = User
    form_class = UserProfileForm
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def test_func(self):
        return (
                self.request.user ==
                self.get_object()
        )

    def get_context_data(
            self,
            **kwargs
    ):
        context = super().get_context_data(
            **kwargs
        )
        context["edit_mode"] = True
        return context

    def get_success_url(self):
        return reverse_lazy(
            "users:profile",
            kwargs={
                "pk": self.object.pk
            }
        )

    def form_valid(
            self,
            form
    ):
        old_steam_id = self.get_object().steam_id
        response = super().form_valid(
            form
        )
        steam_changed = (
                self.object.steam_id
                and self.object.steam_id != old_steam_id
        )
        if steam_changed:
            self.object.steam_sync_status = "waiting"
            self.object.save(
                update_fields=[
                    "steam_sync_status"
                ]
            )
            threading.Thread(
                target=sync_library_background,
                args=(
                    self.object.id,
                ),
                daemon=True,
            ).start()
        return response


class ProfileDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.DeleteView
):
    model = User
    template_name = "users/profile_confirm_delete.html"
    success_url = reverse_lazy("core:home")

    def test_func(self):
        return self.request.user == self.get_object()

    def form_valid(self, form):
        logout(self.request)
        return super().form_valid(form)


class UpdateSteamLibraryView(
    LoginRequiredMixin,
    generic.View
):
    def post(
            self,
            request,
            pk
    ):
        user = request.user
        if not user.steam_id:
            messages.error(
                request,
                "Steam ID is not connected."
            )
            return redirect(
                "users:profile",
                pk=user.pk
            )
        if (
                user.steam_last_update_request
                and timezone.now()
                -
                user.steam_last_update_request
                <
                timedelta(minutes=10)
        ):
            messages.warning(
                request,
                "You can update library only every 10 minutes."
            )
            return redirect(
                "users:profile",
                pk=user.pk
            )
        user.steam_last_update_request = timezone.now()
        user.steam_sync_status = "waiting"
        user.save(
            update_fields=[
                "steam_last_update_request",
                "steam_sync_status",
            ]
        )
        threading.Thread(
            target=sync_library_background,
            args=(
                user.id,
            ),
            daemon=True,
        ).start()
        messages.success(
            request,
            "Steam library update started."
        )
        return redirect(
            "users:profile",
            pk=user.pk
        )
