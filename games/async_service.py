import asyncio

from django.utils import timezone

from games.services import SteamService


async def sync_user_steam_library_async(user):
    user.steam_sync_status = "syncing"
    user.save(
        update_fields=[
            "steam_sync_status"
        ]
    )

    try:
        await asyncio.to_thread(
            SteamService.sync_library,
            user
        )

        user.steam_sync_status = "completed"
        user.steam_last_sync = timezone.now()

    except Exception:
        user.steam_sync_status = "error"

    user.save(
        update_fields=[
            "steam_sync_status",
            "steam_last_sync",
        ]
    )
