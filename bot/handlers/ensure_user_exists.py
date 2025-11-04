from bot.database_client import ensure_user_exists
from bot.handlers.handler import Handler, STATUS, STATE


class EnsureUserExists(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return "message" in update and "from" in update["message"]

    def handle(self, update: dict, state: STATE) -> STATUS:
        telegram_id = update["message"]["from"]["id"]
        ensure_user_exists(telegram_id)
        return STATUS.CONTINUE
