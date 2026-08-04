from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from game_collections.models import CollectionGame, GameCollection
from games.models import Game


class HomeViewTests(TestCase):
    def test_most_used_games_are_ordered_by_collection_count(self):
        owner = get_user_model().objects.create_user(
            username="owner",
            password="password",
        )
        popular_game = Game.objects.create(title="Popular")
        other_game = Game.objects.create(title="Other")
        collections = [
            GameCollection.objects.create(owner=owner, title=f"List {index}")
            for index in range(2)
        ]
        CollectionGame.objects.create(
            collection=collections[0],
            game=popular_game,
        )
        CollectionGame.objects.create(
            collection=collections[1],
            game=popular_game,
        )
        CollectionGame.objects.create(
            collection=collections[0],
            game=other_game,
        )

        response = self.client.get(reverse("core:home"))

        games = list(response.context["most_used_games"])
        self.assertEqual(games[0], popular_game)
        self.assertEqual(games[0].collection_count, 2)
