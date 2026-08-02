import re

from dal import autocomplete
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

from games.models import Game

User = get_user_model()

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Remember your Username",
            }
        ),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Remember your Password",
            }
        ),
    )


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        min_length=8,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Be creative",
            }
        ),
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password1234!",
            }
        ),
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
            }
        ),
    )

    class Meta:
        model = User

        fields = (
            "username",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.help_text = ""

    def clean_password1(self):
        password = self.cleaned_data["password1"]

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"\d", password):
            raise forms.ValidationError(
                "Password must contain at least one number."
            )

        return password


class UserProfileForm(forms.ModelForm):
    favorite_game = forms.ModelChoiceField(
        queryset=Game.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="users:game-autocomplete",
            attrs={
                "data-placeholder": "Search favorite game...",
                "style": "width:100%",
            },
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "gender",
            "age",
            "favorite_game",
            "steam_id",
        )

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "example@gmail.com",
                }
            ),
            "gender": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "age": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your age",
                }
            ),
            "steam_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your Steam ID",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.help_text = ""


class SteamLibrarySearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-field",
                "placeholder": "Search Steam games...",
            }
        ),
    )
