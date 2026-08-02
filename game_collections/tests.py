from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from game_collections.models import CollectionGame, GameCollection
from games.models import Game


class GameCollectionListQueryTests(TestCase):
    def test_list_exposes_annotated_game_count(self):
        user = get_user_model().objects.create_user(
            username="owner",
            password="password",
        )
        collection = GameCollection.objects.create(
            owner=user,
            title="Collection",
        )
        CollectionGame.objects.create(
            collection=collection,
            game=Game.objects.create(title="Game"),
        )

        response = self.client.get(reverse("game_collections:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["collections"][0].games_count, 1)
