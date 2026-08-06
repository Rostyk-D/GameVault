import requests
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone

from games.models import (
    Game,
    Developer,
    Genre,
    UserGame,
)


class SteamServiceError(Exception):
    """Steam API could not provide a reliable response."""


class SteamService:
    IGNORED_APPIDS = [
        365670,
        431960,
    ]

    IGNORED_TYPES = [
        "dlc",
        "demo",
        "application",
        "music",
    ]

    @staticmethod
    def get_owned_games(steam_id):
        url = (
            "https://api.steampowered.com/"
            "IPlayerService/GetOwnedGames/v1/"
        )

        params = {
            "key": settings.STEAM_API_KEY,
            "steamid": steam_id,
            "include_appinfo": True,
            "include_played_free_games": True,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=15,
            )

            response.raise_for_status()

            return (
                response.json()
                .get("response", {})
                .get("games", [])
            )

        except (requests.RequestException, ValueError) as error:
            raise SteamServiceError(
                "Unable to load the Steam library."
            ) from error

    @staticmethod
    def get_game_details(appid):
        url = (
            "https://store.steampowered.com/"
            f"api/appdetails?appids={appid}"
        )

        try:
            response = requests.get(
                url,
                timeout=15,
            )

            response.raise_for_status()

            return (
                response.json()
                .get(str(appid), {})
                .get("data")
            )

        except (requests.RequestException, ValueError) as error:
            raise SteamServiceError(
                f"Unable to load Steam details for app {appid}."
            ) from error

    @staticmethod
    def get_cover(appid, details=None):
        covers = []

        if details:
            image = details.get(
                "header_image"
            )

            if image:
                covers.append(image)

        covers.append(
            (
                "https://shared.fastly.steamstatic.com/"
                f"store_item_assets/steam/apps/{appid}/header.jpg"
            )
        )

        for cover in covers:
            try:
                response = requests.head(
                    cover,
                    timeout=5,
                )

                if response.status_code == 200:
                    return cover

            except requests.RequestException:
                continue

        return None

    @staticmethod
    def get_steam_reviews(appid):
        url = (
            "https://store.steampowered.com/"
            f"appreviews/{appid}?json=1"
        )

        try:
            response = requests.get(
                url,
                timeout=15,
            )

            data = response.json()

            summary = data.get(
                "query_summary",
                {}
            )

            positive = summary.get(
                "total_positive",
                0,
            )

            negative = summary.get(
                "total_negative",
                0,
            )

            total = positive + negative

            score = (
                round(
                    positive / total * 100
                )
                if total
                else 0
            )

            return {
                "positive": positive,
                "negative": negative,
                "score": score,
            }

        except requests.RequestException:
            return {
                "positive": 0,
                "negative": 0,
                "score": 0,
            }

    @classmethod
    async def sync_library(
        cls,
        user,
    ):
        try:
            user.steam_sync_status = "syncing"
            user.steam_sync_progress = 0

            await sync_to_async(user.save)(
                update_fields=[
                    "steam_sync_status",
                    "steam_sync_progress",
                ]
            )

            steam_games = await sync_to_async(
                cls.get_owned_games
            )(
                user.steam_id
            )

            if not steam_games:
                user.steam_library_status = "private"
                user.steam_sync_status = "completed"
                user.steam_last_sync = timezone.now()

                await sync_to_async(user.save)(
                    update_fields=[
                        "steam_library_status",
                        "steam_sync_status",
                        "steam_last_sync",
                    ]
                )

                return

            user.steam_library_status = "public"

            await sync_to_async(user.save)(
                update_fields=[
                    "steam_library_status",
                ]
            )

            processed = 0

            for steam_game in steam_games:
                appid = steam_game.get(
                    "appid"
                )

                if appid in cls.IGNORED_APPIDS:
                    continue

                details = await sync_to_async(
                    cls.get_game_details
                )(
                    appid
                )

                if not details:
                    continue

                if details.get(
                    "type"
                ) in cls.IGNORED_TYPES:
                    continue

                developer = None

                developers = details.get(
                    "developers",
                    [],
                )

                if developers:
                    developer, _ = await sync_to_async(
                        Developer.objects.get_or_create
                    )(
                        name=developers[0]
                    )

                title = details.get(
                    "name",
                    steam_game.get(
                        "name",
                        "Unknown",
                    ),
                )

                game, _ = await sync_to_async(
                    Game.objects.get_or_create
                )(
                    steam_appid=appid,
                    defaults={
                        "title": title,
                    },
                )

                game.title = title

                game.description = details.get(
                    "short_description",
                    "",
                )

                game.cover = await sync_to_async(
                    cls.get_cover
                )(
                    appid,
                    details,
                )

                steam_reviews = await sync_to_async(
                    cls.get_steam_reviews
                )(
                    appid
                )

                game.steam_positive_reviews = (
                    steam_reviews["positive"]
                )

                game.steam_negative_reviews = (
                    steam_reviews["negative"]
                )

                game.steam_review_score = (
                    steam_reviews["score"]
                )

                game.developer = developer

                await sync_to_async(
                    game.save
                )()

                for genre in details.get(
                    "genres",
                    [],
                ):
                    genre_obj, _ = await sync_to_async(
                        Genre.objects.get_or_create
                    )(
                        name=genre["description"]
                    )

                    await sync_to_async(
                        game.genres.add
                    )(
                        genre_obj
                    )

                await sync_to_async(
                    UserGame.objects.update_or_create
                )(
                    user=user,
                    game=game,
                    defaults={
                        "playtime_forever": steam_game.get(
                            "playtime_forever",
                            0,
                        )
                    },
                )

                processed += 1

                user.steam_sync_progress = processed

                await sync_to_async(user.save)(
                    update_fields=[
                        "steam_sync_progress",
                    ]
                )

            user.steam_sync_status = "completed"
            user.steam_last_sync = timezone.now()

            await sync_to_async(user.save)(
                update_fields=[
                    "steam_sync_status",
                    "steam_last_sync",
                ]
            )

        except Exception:
            user.steam_sync_status = "error"

            await sync_to_async(user.save)(
                update_fields=[
                    "steam_sync_status",
                ]
            )
