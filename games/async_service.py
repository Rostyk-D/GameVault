from games.services import SteamService


async def sync_user_steam_library_async(user):
    try:
        return await SteamService.sync_library(user)
    except Exception:
        return None
