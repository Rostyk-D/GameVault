import asyncio
import time
from datetime import datetime

import requests
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from games.models import (
    Developer,
    Game,
    Genre,
    UserGame,
)


class SteamServiceError(Exception):
    """Steam API could not provide a reliable response."""


class SteamService:
    IGNORED_APPIDS = {
        365670,
        431960,
    }

    IGNORED_TYPES = {
        "dlc",
        "demo",
        "application",
        "music",
    }

    MAX_CONCURRENT_REQUESTS = 8
    REQUEST_RETRIES = 3
    SUCCESS_THRESHOLD = 0.90

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

            data = response.json()
            response_data = data.get("response", {})

            return response_data.get("games", [])

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

        last_error = None

        for attempt in range(
            SteamService.REQUEST_RETRIES
        ):
            try:
                response = requests.get(
                    url,
                    timeout=15,
                )
                response.raise_for_status()

                data = response.json()
                app_data = data.get(
                    str(appid),
                    {},
                )

                if not app_data.get("success"):
                    return None

                return app_data.get("data")

            except (
                requests.RequestException,
                ValueError,
            ) as error:
                last_error = error

                if attempt < (
                    SteamService.REQUEST_RETRIES - 1
                ):
                    time.sleep(2 ** attempt)

        raise SteamServiceError(
            f"Unable to load Steam details for app {appid}."
        ) from last_error

    @staticmethod
    def get_cover(details):
        if not details:
            return None

        return details.get("header_image")

    @staticmethod
    def get_last_played(steam_game):
        timestamp = steam_game.get(
            "rtime_last_played"
        )

        if not timestamp:
            return None

        try:
            return datetime.fromtimestamp(
                int(timestamp),
                tz=timezone.get_current_timezone(),
            )
        except (
            TypeError,
            ValueError,
            OSError,
        ):
            return None

    @staticmethod
    def make_unique_slug(
        title,
        reserved_slugs,
    ):
        base_slug = slugify(title) or "game"
        base_slug = base_slug[:150]

        slug = base_slug
        suffix_number = 1

        while slug in reserved_slugs:
            suffix = f"-{suffix_number}"

            slug = (
                f"{base_slug[:150 - len(suffix)]}"
                f"{suffix}"
            )

            suffix_number += 1

        reserved_slugs.add(slug)

        return slug

    @classmethod
    async def get_existing_games(
        cls,
        appids,
    ):
        return await sync_to_async(
            lambda: list(
                Game.objects.filter(
                    steam_appid__in=appids
                )
            )
        )()

    @classmethod
    async def fetch_game_details(
        cls,
        appid,
        semaphore,
    ):
        async with semaphore:
            try:
                details = await sync_to_async(
                    cls.get_game_details,
                    thread_sensitive=False,
                )(appid)

                return (
                    appid,
                    details,
                    None,
                )

            except SteamServiceError as error:
                return (
                    appid,
                    None,
                    str(error),
                )

            except Exception as error:
                return (
                    appid,
                    None,
                    f"Unexpected error: {error}",
                )

    @classmethod
    async def save_sync_status(
        cls,
        user,
        status=None,
        progress=None,
        library_status=None,
        last_sync=False,
    ):
        update_fields = []

        if status is not None:
            user.steam_sync_status = status
            update_fields.append(
                "steam_sync_status"
            )

        if progress is not None:
            user.steam_sync_progress = progress
            update_fields.append(
                "steam_sync_progress"
            )

        if library_status is not None:
            user.steam_library_status = (
                library_status
            )
            update_fields.append(
                "steam_library_status"
            )

        if last_sync:
            user.steam_last_sync = timezone.now()
            update_fields.append(
                "steam_last_sync"
            )

        if update_fields:
            await sync_to_async(
                user.save
            )(
                update_fields=update_fields
            )

    @classmethod
    async def sync_library(
        cls,
        user,
    ):
        try:
            print(
                "\n=== STEAM LIBRARY SYNC STARTED ==="
            )

            await cls.save_sync_status(
                user,
                status="syncing",
                progress=0,
            )

            # -------------------------------------------------
            # 1. Get Steam library
            # -------------------------------------------------

            steam_games = await sync_to_async(
                cls.get_owned_games,
                thread_sensitive=False,
            )(
                user.steam_id
            )

            if not steam_games:
                await cls.save_sync_status(
                    user,
                    status="completed",
                    progress=0,
                    library_status="private",
                    last_sync=True,
                )

                print(
                    "Steam library is empty or private."
                )
                print(
                    "=== STEAM LIBRARY SYNC FINISHED ===\n"
                )

                return {
                    "total": 0,
                    "existing": 0,
                    "new": 0,
                    "failed": 0,
                    "success_rate": 100,
                    "errors": [],
                }

            await cls.save_sync_status(
                user,
                library_status="public",
            )

            # -------------------------------------------------
            # 2. Filter Steam games
            # -------------------------------------------------

            filtered_games = []

            for steam_game in steam_games:
                appid = steam_game.get("appid")

                if not appid:
                    continue

                if appid in cls.IGNORED_APPIDS:
                    continue

                filtered_games.append(
                    steam_game
                )

            total_games = len(filtered_games)

            if not filtered_games:
                await cls.save_sync_status(
                    user,
                    status="completed",
                    progress=0,
                    last_sync=True,
                )

                print(
                    "No valid games found in Steam library."
                )
                print(
                    "=== STEAM LIBRARY SYNC FINISHED ===\n"
                )

                return {
                    "total": 0,
                    "existing": 0,
                    "new": 0,
                    "failed": 0,
                    "success_rate": 100,
                    "errors": [],
                }

            # -------------------------------------------------
            # 3. Get all Steam AppIDs
            # -------------------------------------------------

            steam_appids = {
                game["appid"]
                for game in filtered_games
            }

            print(
                f"Steam games found: {total_games}"
            )

            # -------------------------------------------------
            # 4. One DB query for existing games
            # -------------------------------------------------

            existing_games = (
                await cls.get_existing_games(
                    steam_appids
                )
            )

            existing_games_by_appid = {
                game.steam_appid: game
                for game in existing_games
            }

            missing_appids = [
                appid
                for appid in steam_appids
                if appid not in existing_games_by_appid
            ]

            print(
                f"Already in database: "
                f"{len(existing_games)}"
            )

            print(
                f"Missing from database: "
                f"{len(missing_appids)}"
            )

            # -------------------------------------------------
            # 5. Fetch Steam details ONLY for new games
            # -------------------------------------------------

            details_by_appid = {}
            failed_games = []
            ignored_games = []

            if missing_appids:
                semaphore = asyncio.Semaphore(
                    cls.MAX_CONCURRENT_REQUESTS
                )

                tasks = [
                    cls.fetch_game_details(
                        appid,
                        semaphore,
                    )
                    for appid in missing_appids
                ]

                results = await asyncio.gather(
                    *tasks
                )

                for (
                    appid,
                    details,
                    error,
                ) in results:

                    if error:
                        failed_games.append(
                            {
                                "appid": appid,
                                "error": error,
                            }
                        )
                        continue

                    if not details:
                        failed_games.append(
                            {
                                "appid": appid,
                                "error": (
                                    "Steam returned "
                                    "no game details."
                                ),
                            }
                        )
                        continue

                    game_type = details.get(
                        "type"
                    )

                    if game_type in cls.IGNORED_TYPES:
                        ignored_games.append(
                            {
                                "appid": appid,
                                "type": game_type,
                            }
                        )
                        continue

                    details_by_appid[appid] = details

            # -------------------------------------------------
            # 6. Developers
            # -------------------------------------------------

            developer_names = set()

            for details in details_by_appid.values():
                developers = details.get(
                    "developers",
                    [],
                )

                if developers:
                    developer_names.add(
                        developers[0]
                    )

            existing_developers = await sync_to_async(
                lambda: list(
                    Developer.objects.filter(
                        name__in=developer_names
                    )
                )
            )()

            developers_by_name = {
                developer.name: developer
                for developer in existing_developers
            }

            missing_developer_names = (
                developer_names
                - set(developers_by_name)
            )

            if missing_developer_names:
                new_developers = [
                    Developer(
                        name=name
                    )
                    for name in missing_developer_names
                ]

                await sync_to_async(
                    Developer.objects.bulk_create
                )(
                    new_developers,
                    ignore_conflicts=True,
                )

                created_developers = await sync_to_async(
                    lambda: list(
                        Developer.objects.filter(
                            name__in=missing_developer_names
                        )
                    )
                )()

                developers_by_name.update(
                    {
                        developer.name: developer
                        for developer in created_developers
                    }
                )

            # -------------------------------------------------
            # 7. Prepare new Game objects
            # -------------------------------------------------

            reserved_slugs = await sync_to_async(
                lambda: set(
                    Game.objects.values_list(
                        "slug",
                        flat=True,
                    )
                )
            )()

            steam_games_by_appid = {
                game["appid"]: game
                for game in filtered_games
            }

            new_games = []

            for appid, details in (
                details_by_appid.items()
            ):
                steam_game = (
                    steam_games_by_appid.get(
                        appid
                    )
                )

                if not steam_game:
                    continue

                title = (
                    details.get("name")
                    or steam_game.get(
                        "name",
                        "Unknown",
                    )
                )

                developer = None

                developers = details.get(
                    "developers",
                    [],
                )

                if developers:
                    developer = (
                        developers_by_name.get(
                            developers[0]
                        )
                    )

                new_games.append(
                    Game(
                        title=title,
                        slug=cls.make_unique_slug(
                            title,
                            reserved_slugs,
                        ),
                        description=details.get(
                            "short_description",
                            "",
                        ),
                        cover=cls.get_cover(
                            details
                        ),
                        steam_appid=appid,
                        developer=developer,
                    )
                )

            # -------------------------------------------------
            # 8. Create new games in one query
            # -------------------------------------------------

            if new_games:
                await sync_to_async(
                    Game.objects.bulk_create
                )(
                    new_games,
                    batch_size=100,
                )

                created_games = await sync_to_async(
                    lambda: list(
                        Game.objects.filter(
                            steam_appid__in=[
                                game.steam_appid
                                for game in new_games
                            ]
                        )
                    )
                )()

                existing_games_by_appid.update(
                    {
                        game.steam_appid: game
                        for game in created_games
                    }
                )

            # -------------------------------------------------
            # 9. Genres
            # -------------------------------------------------

            genre_names = set()

            for details in details_by_appid.values():
                for genre in details.get(
                    "genres",
                    [],
                ):
                    name = genre.get(
                        "description"
                    )

                    if name:
                        genre_names.add(name)

            existing_genres = await sync_to_async(
                lambda: list(
                    Genre.objects.filter(
                        name__in=genre_names
                    )
                )
            )()

            genres_by_name = {
                genre.name: genre
                for genre in existing_genres
            }

            missing_genre_names = (
                genre_names
                - set(genres_by_name)
            )

            if missing_genre_names:
                new_genres = [
                    Genre(
                        name=name
                    )
                    for name in missing_genre_names
                ]

                await sync_to_async(
                    Genre.objects.bulk_create
                )(
                    new_genres,
                    ignore_conflicts=True,
                )

                created_genres = await sync_to_async(
                    lambda: list(
                        Genre.objects.filter(
                            name__in=missing_genre_names
                        )
                    )
                )()

                genres_by_name.update(
                    {
                        genre.name: genre
                        for genre in created_genres
                    }
                )

            # -------------------------------------------------
            # 10. Create Game <-> Genre relations
            # -------------------------------------------------

            new_game_ids = {
                game.id
                for game in new_games
                if game.id
            }

            if new_game_ids:
                through_model = (
                    Game.genres.through
                )

                genre_relations = []

                for appid, details in (
                    details_by_appid.items()
                ):
                    game = (
                        existing_games_by_appid.get(
                            appid
                        )
                    )

                    if not game:
                        continue

                    if game.id not in new_game_ids:
                        continue

                    for genre in details.get(
                        "genres",
                        [],
                    ):
                        genre_name = genre.get(
                            "description"
                        )

                        genre_obj = (
                            genres_by_name.get(
                                genre_name
                            )
                        )

                        if genre_obj:
                            genre_relations.append(
                                through_model(
                                    game_id=game.id,
                                    genre_id=genre_obj.id,
                                )
                            )

                if genre_relations:
                    await sync_to_async(
                        through_model.objects.bulk_create
                    )(
                        genre_relations,
                        ignore_conflicts=True,
                        batch_size=200,
                    )

            # -------------------------------------------------
            # 11. Create UserGame records
            # -------------------------------------------------

            user_games = []

            for steam_game in filtered_games:
                appid = steam_game["appid"]

                game = (
                    existing_games_by_appid.get(
                        appid
                    )
                )

                if not game:
                    continue

                user_games.append(
                    UserGame(
                        user=user,
                        game=game,
                        playtime_forever=(
                            steam_game.get(
                                "playtime_forever",
                                0,
                            )
                        ),
                        last_played=(
                            cls.get_last_played(
                                steam_game
                            )
                        ),
                    )
                )

            if user_games:
                await sync_to_async(
                    UserGame.objects.bulk_create
                )(
                    user_games,
                    ignore_conflicts=True,
                    batch_size=200,
                )

            # -------------------------------------------------
            # 12. Update existing UserGame records
            # -------------------------------------------------

            game_ids = [
                game.id
                for game in (
                    existing_games_by_appid.values()
                )
            ]

            existing_user_games = await sync_to_async(
                lambda: {
                    user_game.game_id: user_game
                    for user_game in (
                        UserGame.objects.filter(
                            user=user,
                            game_id__in=game_ids,
                        )
                    )
                }
            )()

            user_games_to_update = []

            for steam_game in filtered_games:
                appid = steam_game["appid"]

                game = (
                    existing_games_by_appid.get(
                        appid
                    )
                )

                if not game:
                    continue

                user_game = (
                    existing_user_games.get(
                        game.id
                    )
                )

                if not user_game:
                    continue

                user_game.playtime_forever = (
                    steam_game.get(
                        "playtime_forever",
                        0,
                    )
                )

                user_game.last_played = (
                    cls.get_last_played(
                        steam_game
                    )
                )

                user_games_to_update.append(
                    user_game
                )

            if user_games_to_update:
                await sync_to_async(
                    UserGame.objects.bulk_update
                )(
                    user_games_to_update,
                    [
                        "playtime_forever",
                        "last_played",
                    ],
                    batch_size=200,
                )

            # -------------------------------------------------
            # 13. Calculate result
            # -------------------------------------------------

            successful_games = (
                len(existing_games)
                + len(new_games)
            )

            unsuccessful_games = (
                total_games
                - successful_games
            )

            success_rate = (
                successful_games / total_games
                if total_games
                else 1
            )

            success_percent = round(
                success_rate * 100
            )

            processed = successful_games

            await cls.save_sync_status(
                user,
                progress=processed,
            )

            # -------------------------------------------------
            # 14. Log problems
            # -------------------------------------------------

            print(
                "\n=== STEAM SYNC RESULT ==="
            )

            print(
                f"Total games: {total_games}"
            )

            print(
                f"Already existed: "
                f"{len(existing_games)}"
            )

            print(
                f"New games: "
                f"{len(new_games)}"
            )

            print(
                f"Failed games: "
                f"{len(failed_games)}"
            )

            print(
                f"Ignored games: "
                f"{len(ignored_games)}"
            )

            print(
                f"Success rate: "
                f"{success_percent}%"
            )

            if failed_games:
                print(
                    "\n=== STEAM SYNC ERRORS ==="
                )

                for failed_game in failed_games:
                    print(
                        f"AppID "
                        f"{failed_game['appid']}: "
                        f"{failed_game['error']}"
                    )

                print(
                    "=== END STEAM SYNC ERRORS ==="
                )

            if ignored_games:
                print(
                    "\n=== STEAM SYNC IGNORED ==="
                )

                for ignored_game in ignored_games:
                    print(
                        f"AppID "
                        f"{ignored_game['appid']}: "
                        f"type="
                        f"{ignored_game['type']}"
                    )

                print(
                    "=== END STEAM SYNC IGNORED ==="
                )

            print(
                "=== STEAM SYNC FINISHED ===\n"
            )

            # -------------------------------------------------
            # 15. Final status
            # -------------------------------------------------

            if success_rate >= cls.SUCCESS_THRESHOLD:
                status = "completed"
            else:
                status = "completed_with_errors"

            await cls.save_sync_status(
                user,
                status=status,
                progress=processed,
                last_sync=True,
            )

            return {
                "total": total_games,
                "existing": len(existing_games),
                "new": len(new_games),
                "failed": len(failed_games),
                "ignored": len(ignored_games),
                "successful": successful_games,
                "success_rate": success_percent,
                "errors": failed_games,
            }

        except SteamServiceError:
            await cls.save_sync_status(
                user,
                status="error",
            )

            print(
                "\n=== STEAM SYNC CRITICAL ERROR ==="
            )

            print(
                "Unable to synchronize Steam library."
            )

            print(
                "=== END STEAM SYNC CRITICAL ERROR ===\n"
            )

            raise

        except Exception as error:
            await cls.save_sync_status(
                user,
                status="error",
            )

            print(
                "\n=== STEAM SYNC UNEXPECTED ERROR ==="
            )

            print(
                f"{type(error).__name__}: {error}"
            )

            print(
                "=== END STEAM SYNC UNEXPECTED ERROR ===\n"
            )

            raise
