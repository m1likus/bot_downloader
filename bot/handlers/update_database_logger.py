import bot.database_client
from bot.handlers.handler import Handler, STATUS, STATE


class UpdateDatabaseLogger(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return True

    def handle(self, update: dict, state: STATE) -> STATUS:
        bot.database_client.persist_updates(update)
        return STATUS.CONTINUE
