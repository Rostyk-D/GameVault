from django.urls import path

from users.views import (
    RegisterView,
    LoginView,
    ProfileDetailView,
    ProfileUpdateView,
    GameAutocomplete,
    UpdateSteamLibraryView,
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
        "games-autocomplete/",
        GameAutocomplete.as_view(),
        name="games-autocomplete",
    ),
    path(
        "profile/<int:pk>/steam-update/",
        UpdateSteamLibraryView.as_view(),
        name="steam-update",
    ),
]
