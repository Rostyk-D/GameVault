from games.services import SteamService


async def sync_user_steam_library_async(user):
    user.steam_sync_status = "syncing"
    user.save(
        update_fields=[
            "steam_sync_status"
        ]
    )

    try:
        await SteamService.sync_library(user)
    except Exception:
        user.steam_sync_status = "error"

    user.save(
        update_fields=[
            "steam_sync_status",
        ]
    )
