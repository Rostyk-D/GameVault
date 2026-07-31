from django.contrib.auth import views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView

from users.forms import (
    UserRegistrationForm,
    UserLoginForm,
)
from users.models import User


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class LoginView(views.LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"


class ProfileDetailView(
    LoginRequiredMixin,
    DetailView
):
    model = User
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def get_object(self):
        return get_object_or_404(
            User,
            pk=self.kwargs["pk"]
        )
