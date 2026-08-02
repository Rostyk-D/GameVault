from django import forms

from game_collections.models import GameCollection


class GameCollectionForm(forms.ModelForm):
    class Meta:
        model = GameCollection

        fields = [
            "title",
            "description",
            "is_public",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-field",
                    "placeholder": "Collection title...",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-field",
                    "placeholder": "Describe your collection...",
                    "rows": 5,
                }
            ),

            "is_public": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class SearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-field",
                "placeholder": "Search...",
            }
        ),
    )
