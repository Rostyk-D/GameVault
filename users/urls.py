from django.urls import path

from users.views import (
    RegisterView,
    LoginView,
    ProfileDetailView,
    ProfileUpdateView,
    GameAutocomplete,
    UpdateSteamLibraryView,
    ProfileDeleteView,
)

app_name = "users"

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "profile/<int:pk>/",
        ProfileDetailView.as_view(),
        name="profile",
    ),
    path(
        "profile/<int:pk>/edit/",
        ProfileUpdateView.as_view(),
        name="profile-edit",
    ),
    path(
        "profile/<int:pk>/delete/",
        ProfileDeleteView.as_view(),
        name="profile-delete"
    ),

    path(
        "game-autocomplete/",
        GameAutocomplete.as_view(),
        name="game-autocomplete",
    ),
    path(
        "profile/<int:pk>/steam-update/",
        UpdateSteamLibraryView.as_view(),
        name="steam-update",
    ),
]
