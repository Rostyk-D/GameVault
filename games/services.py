import requests

from django.conf import settings
from django.utils.text import slugify

from games.models import (
    Game,
    Developer,
    Genre,
    UserGame,
)


class SteamService:
    IGNORED_APPIDS = [
        365670,  # Blender
        431960,  # Wallpaper Engine
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
                timeout=10,
            )

            return (
                response
                .json()
                .get("response", {})
                .get("games", [])
            )

        except requests.RequestException:
            return []

    @staticmethod
    def get_game_details(appid):
        url = (
            "https://store.steampowered.com/"
            f"api/appdetails?appids={appid}"
        )

        try:
            response = requests.get(
                url,
                timeout=10,
            )

            data = response.json()

            return (
                data
                .get(str(appid), {})
                .get("data")
            )

        except requests.RequestException:
            return None

    @staticmethod
    def get_cover(appid, details=None):

        covers = []

        if details:
            header = details.get(
                "header_image"
            )

            if header:
                covers.append(header)

        covers.extend(
            [
                f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
                f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
                f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
            ]
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
    def create_slug(title, appid):
        return (
            f"{slugify(title)}-{appid}"
        )

    @classmethod
    def sync_library(cls, user):

        steam_games = cls.get_owned_games(
            user.steam_id
        )

        created = 0

        for steam_game in steam_games:

            appid = steam_game["appid"]

            if appid in cls.IGNORED_APPIDS:
                continue

            details = cls.get_game_details(
                appid
            )

            if not details:
                continue

            if details.get("type") in cls.IGNORED_TYPES:
                continue

            developer = None

            developers = details.get(
                "developers",
                []
            )

            if developers:
                developer, _ = (
                    Developer.objects.get_or_create(
                        name=developers[0]
                    )
                )

            game, is_created = (
                Game.objects.get_or_create(
                    steam_appid=appid,
                    defaults={
                        "title": details.get(
                            "name",
                            steam_game.get(
                                "name",
                                "Unknown"
                            )
                        ),
                        "slug": cls.create_slug(
                            details.get(
                                "name",
                                "unknown"
                            ),
                            appid,
                        ),
                    }
                )
            )

            game.title = details.get(
                "name",
                game.title
            )

            game.description = details.get(
                "short_description",
                ""
            )

            game.cover = cls.get_cover(
                appid,
                details
            )

            game.developer = developer

            game.save()

            for genre in details.get(
                "genres",
                []
            ):

                genre_obj, _ = (
                    Genre.objects.get_or_create(
                        name=genre["description"]
                    )
                )

                game.genres.add(
                    genre_obj
                )

            UserGame.objects.update_or_create(
                user=user,
                game=game,
                defaults={
                    "playtime_forever": steam_game.get(
                        "playtime_forever",
                        0
                    )
                }
            )

            if is_created:
                created += 1

        return created

    @classmethod
    def update_game_covers(cls):

        updated = 0

        for game in Game.objects.all():

            details = cls.get_game_details(
                game.steam_appid
            )

            if not details:
                continue

            cover = cls.get_cover(
                game.steam_appid,
                details
            )

            if cover and game.cover != cover:

                game.cover = cover

                game.save(
                    update_fields=[
                        "cover"
                    ]
                )

                updated += 1

        return updated
