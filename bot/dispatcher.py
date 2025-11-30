from bot.handlers.handler import Handler
import bot.database_client
from bot.types import STATUS


class Dispatcher:
    def __init__(self):
        self._handlers: list[Handler] = []

    def add_handlers(self, *handlers: list[Handler]) -> None:
        for handler in handlers:
            self._handlers.append(handler)

    def _get_telegram_id_from_update(self, update: dict) -> int:
        if "message" in update:
            return update["message"]["from"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["from"]["id"]
        return None

    async def dispatch(self, update: dict) -> None:
        telegram_id = self._get_telegram_id_from_update(update)
        user = await bot.database_client.get_user(telegram_id) if telegram_id else None
        user_state = user.get("state") if user else None

        for handler in self._handlers:
            if handler.can_handle(update, user_state):
                if await handler.handle(update, user_state) == STATUS.STOP:
                    break
