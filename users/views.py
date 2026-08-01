from dal import autocomplete
from django.contrib.auth import views
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin
)
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from games.models import Game
from users.forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
)
from users.models import User


class RegisterView(generic.CreateView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


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
        return qs


class ProfileDetailView(
    LoginRequiredMixin,
    generic.DetailView
):
    model = User
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def get_object(self):
        return get_object_or_404(
            User,
            pk=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user == self.object:
            context["form"] = UserProfileForm(
                instance=self.object
            )

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
        return self.request.user == self.get_object()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edit_mode"] = True
        return context

    def get_success_url(self):
        return reverse_lazy(
            "users:profile",
            kwargs={
                "pk": self.object.pk
            }
        )
