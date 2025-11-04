import bot.telegram_api_client
import bot.database_client
import json
from bot.handlers.handler import Handler, STATUS, STATE


class MessageStart(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return (
            "message" in update
            and "text" in update["message"]
            and update["message"]["text"] == "/start"
        )

    def handle(self, update: dict, state: STATE) -> STATUS:
        telegram_id = update["message"]["from"]["id"]
        bot.database_client.clear_user_state_and_video(telegram_id)
        bot.database_client.update_user_state(telegram_id, "WAIT_FOR_TOKEN")

        bot.telegram_api_client.send_message(
            chat_id=update["message"]["chat"]["id"],
            text="Этот бот способен скачивать видео с видеохостингов: Youtube, Rutube, Vkvideo",
            reply_markup=json.dumps({"remove_keyboard": True}),
        )

        bot.telegram_api_client.send_message(
            chat_id=update["message"]["chat"]["id"],
            text="Пришлите ссылку на видео или video Id",
        )
        return STATUS.STOP
