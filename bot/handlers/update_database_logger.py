import bot.database_client
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS


class UpdateDatabaseLogger(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return True

    async def handle(self, update: dict, state: STATE) -> STATUS:
        await bot.database_client.persist_updates(update)
        return STATUS.CONTINUE
