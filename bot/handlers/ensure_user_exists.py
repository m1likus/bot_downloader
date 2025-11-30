from bot.database_client import ensure_user_exists
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS


class EnsureUserExists(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return "message" in update and "from" in update["message"]

    async def handle(self, update: dict, state: STATE) -> STATUS:
        telegram_id = update["message"]["from"]["id"]
        await ensure_user_exists(telegram_id)
        return STATUS.CONTINUE
