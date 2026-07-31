from django.contrib.auth import views
from django.urls import reverse_lazy
from django.views.generic import CreateView

from users.forms import UserRegistrationForm, UserLoginForm


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")


class LoginView(views.LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"
