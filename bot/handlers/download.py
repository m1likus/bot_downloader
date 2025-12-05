import bot.telegram_api_client
import bot.database_client
import traceback
from bot.download_utils import DownloadUtils
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS


class DownloadHandler(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return (
            "callback_query" in update
            and update["callback_query"]["data"].startswith("type_")
            and state == STATE.WAIT_FOR_AUDIO.value
        )

    async def handle(self, update: dict, state: STATE) -> STATUS:
        callback_query = update["callback_query"]
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        telegram_id = callback_query["from"]["id"]
        callback_data = callback_query["data"]
        type = callback_data.replace("type_", "")

        await bot.database_client.update_user_video_type(telegram_id, type)
        await bot.database_client.update_user_state(
            telegram_id, STATE.WAIT_FOR_START_DOWNLOADING
        )

        user_data = await bot.database_client.get_user(telegram_id)
        await bot.telegram_api_client.delete_message(chat_id, message_id)

        await self._start_download_process(chat_id, telegram_id, user_data)

        await bot.telegram_api_client.answer_callback_query(callback_query["id"])
        return STATUS.STOP

    async def _start_download_process(self, chat_id: int, telegram_id: int, user_data):
        # Начинает процесс скачивания: генерирует формат и отправляет задачку в RabbitMQ
        ydl_format = DownloadUtils._generate_ydl_format(
            user_data["video_res"], user_data["video_type"]
        )

        download_task = {
            "telegram_id": telegram_id,
            "chat_id": chat_id,
            "url": user_data["url"],
            "resolution": user_data["video_res"],
            "type": user_data["video_type"],
            "ydl_format": ydl_format,
        }

        try:
            await DownloadUtils._send_to_rabbitmq(download_task)
            await DownloadUtils._show_download_started(chat_id, user_data)

        except Exception:
            traceback.print_exc()
            await bot.database_client.clear_user_video_and_set_state(telegram_id)
            error_message = "Ошибка при запуске скачивания. Начните заново."
            await bot.telegram_api_client.send_message(
                chat_id=chat_id, text=error_message
            )
