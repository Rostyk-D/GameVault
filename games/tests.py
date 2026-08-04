from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from game_collections.models import CollectionGame, GameCollection
from games.models import CommentVote, Game, GameComment, Genre


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
