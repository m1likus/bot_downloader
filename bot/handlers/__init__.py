from bot.handlers.handler import Handler
from bot.handlers.update_database_logger import UpdateDatabaseLogger
from bot.handlers.ensure_user_exists import EnsureUserExists
from bot.handlers.message_start import MessageStart
from bot.handlers.url import UrlHandler
from bot.handlers.get_res import ResHandler
from bot.handlers.download import DownloadHandler


def get_handlers() -> list[Handler]:
    return [
        UpdateDatabaseLogger(),
        EnsureUserExists(),
        MessageStart(),
        UrlHandler(),
        ResHandler(),
        DownloadHandler(),
    ]
