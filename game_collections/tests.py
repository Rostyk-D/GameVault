from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from game_collections.models import (
    CollectionGame,
    CollectionVote,
    GameCollection,
)
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

    def test_list_counts_each_vote_once_when_collection_has_many_games(self):
        owner = get_user_model().objects.create_user(
            username="owner",
            password="password",
        )
        voter = get_user_model().objects.create_user(
            username="voter",
            password="password",
        )
        collection = GameCollection.objects.create(
            owner=owner,
            title="Collection",
        )
        games = Game.objects.bulk_create(
            [
                Game(
                    title=f"Game {number}",
                    slug=f"game-{number}",
                )
                for number in range(13)
            ]
        )
        CollectionGame.objects.bulk_create(
            [
                CollectionGame(collection=collection, game=game)
                for game in games
            ]
        )
        CollectionVote.objects.create(
            user=voter,
            collection=collection,
            value=CollectionVote.DISLIKE,
        )

        response = self.client.get(reverse("game_collections:list"))

        result = response.context["collections"][0]
        self.assertEqual(result.dislikes, 1)
        self.assertEqual(result.reputation, -1)
