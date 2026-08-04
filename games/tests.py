from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import requests
from unittest.mock import Mock, patch

from game_collections.models import CollectionGame, GameCollection
from games.models import CommentVote, Game, GameComment, Genre
from games.services import SteamService, SteamServiceError


class GameDetailQueryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer",
            password="password",
        )
        self.game = Game.objects.create(title="Game")
        self.game.genres.add(Genre.objects.create(name="RPG"))
        collection = GameCollection.objects.create(
            owner=self.user,
            title="My collection",
        )
        CollectionGame.objects.create(collection=collection, game=self.game)

        for index in range(15):
            author = get_user_model().objects.create_user(
                username=f"author-{index}",
                password="password",
            )
            comment = GameComment.objects.create(
                game=self.game,
                user=author,
                text="Comment",
            )
            CommentVote.objects.create(
                comment=comment,
                user=self.user,
                value=CommentVote.LIKE,
            )

    def test_detail_uses_prefetched_votes_and_collection_membership(self):
        self.client.force_login(self.user)

        # The number is independent of the number of comments on the page.
        with self.assertNumQueries(9):
            response = self.client.get(
                reverse("games:game-detail", kwargs={"pk": self.game.pk})
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_collections"][0].has_game)
        self.assertTrue(
            all(
                comment.user_vote == CommentVote.LIKE
                for comment in response.context["comments"]
            )
        )

    def test_collection_selection_removes_unchecked_game_membership(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "game_collections:add-game-from-page",
                kwargs={"game_id": self.game.pk},
            ),
            {"collections": []},
        )

        self.assertRedirects(
            response,
            reverse("games:game-detail", kwargs={"pk": self.game.pk}),
        )
        self.assertFalse(
            CollectionGame.objects.filter(
                collection__owner=self.user,
                game=self.game,
            ).exists()
        )


class GameModelTests(TestCase):
    def test_duplicate_titles_receive_unique_slugs(self):
        first = Game.objects.create(title="A Game")
        second = Game.objects.create(title="A Game")

        self.assertEqual(first.slug, "a-game")
        self.assertEqual(second.slug, "a-game-1")


class SteamServiceTests(TestCase):
    @patch("games.services.requests.get")
    def test_get_owned_games_uses_provided_steam_id(self, mock_get):
        response = Mock()
        response.json.return_value = {
            "response": {"games": [{"appid": 10}]}
        }
        mock_get.return_value = response

        games = SteamService.get_owned_games("76561198402195386")

        self.assertEqual(games, [{"appid": 10}])
        self.assertEqual(
            mock_get.call_args.kwargs["params"]["steamid"],
            "76561198402195386",
        )

    @patch("games.services.requests.get")
    def test_get_owned_games_raises_on_unavailable_steam_api(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()

        with self.assertRaises(SteamServiceError):
            SteamService.get_owned_games("76561198402195386")
