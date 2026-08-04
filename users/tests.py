from django.contrib.auth import get_user_model
from django.test import TestCase

from users.forms import UserProfileForm


class UserProfileFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="player",
            password="password",
        )

    def test_accepts_and_normalizes_valid_steam_id64(self):
        form = UserProfileForm(
            data={
                "email": "player@example.com",
                "gender": "",
                "age": "",
                "favorite_game": "",
                "steam_id": " 76561198402195386 ",
            },
            instance=self.user,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["steam_id"], "76561198402195386")

    def test_rejects_non_steam_id64_value(self):
        form = UserProfileForm(
            data={
                "email": "player@example.com",
                "gender": "",
                "age": "",
                "favorite_game": "",
                "steam_id": "invalid-id",
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("steam_id", form.errors)
