from django import forms

from games.models import GameComment


class GameSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search games...",
            }
        ),
    )


class GameCommentForm(forms.ModelForm):

    class Meta:
        model = GameComment

        fields = [
            "text",
        ]

        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Write your opinion...",
                    "rows": 4,
                }
            )
        }
