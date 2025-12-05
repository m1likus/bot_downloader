import bot.telegram_api_client
import bot.database_client
import json
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS


class MessageStart(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return (
            "message" in update
            and "text" in update["message"]
            and (update["message"]["text"] == "/start" or state is None)
        )

    async def handle(self, update: dict, state: STATE) -> STATUS:
        telegram_id = update["message"]["from"]["id"]
        await bot.database_client.clear_user_video_and_set_state(telegram_id)

        await bot.telegram_api_client.send_message(
            chat_id=update["message"]["chat"]["id"],
            text="Этот бот способен скачивать видео с видеохостингов: YouTube, Rutube, VKVideo. Пришлите YouTube video-id или ссылку на видео.",
            reply_markup=json.dumps({"remove_keyboard": True}),
        )
        return STATUS.STOP
