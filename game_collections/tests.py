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
    def test_collections_receive_unique_slugs_and_use_them_in_urls(self):
        user = get_user_model().objects.create_user(
            username="owner",
            password="password",
        )
        first = GameCollection.objects.create(owner=user, title="My list")
        second = GameCollection.objects.create(owner=user, title="My list")

        self.assertEqual(first.slug, "my-list")
        self.assertEqual(second.slug, "my-list-1")
        response = self.client.get(
            reverse("game_collections:detail", kwargs={"slug": first.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_collection_slug_does_not_conflict_with_create_route(self):
        user = get_user_model().objects.create_user(
            username="owner",
            password="password",
        )

        collection = GameCollection.objects.create(owner=user, title="Create")

        self.assertEqual(collection.slug, "create-1")

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

    def test_game_membership_sync_does_not_modify_other_users_collections(self):
        owner = get_user_model().objects.create_user(
            username="owner",
            password="password",
        )
        other_user = get_user_model().objects.create_user(
            username="other",
            password="password",
        )
        game = Game.objects.create(title="Game")
        owner_collection = GameCollection.objects.create(
            owner=owner,
            title="Owner list",
        )
        other_collection = GameCollection.objects.create(
            owner=other_user,
            title="Other list",
        )
        CollectionGame.objects.create(collection=owner_collection, game=game)
        CollectionGame.objects.create(collection=other_collection, game=game)

        self.client.force_login(owner)
        self.client.post(
            reverse(
                "game_collections:add-game-from-page",
                kwargs={"game_id": game.pk},
            ),
            {"collections": []},
        )

        self.assertFalse(
            CollectionGame.objects.filter(
                collection=owner_collection,
                game=game,
            ).exists()
        )
        self.assertTrue(
            CollectionGame.objects.filter(
                collection=other_collection,
                game=game,
            ).exists()
        )
