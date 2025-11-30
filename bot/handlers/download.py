import bot.telegram_api_client
import bot.database_client
import aio_pika
import traceback
import json
import os
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
        ydl_format = self._generate_ydl_format(
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
            await self._send_to_rabbitmq(download_task)
            await self._show_download_started(chat_id, user_data)

        except Exception:
            traceback.print_exc()
            await bot.database_client.clear_user_video_and_set_state(telegram_id)
            error_message = "Ошибка при запуске скачивания. Начните заново."
            await bot.telegram_api_client.send_message(
                chat_id=chat_id, text=error_message
            )

    def _generate_ydl_format(self, res: str, type: str) -> str:
        # Генерирует ydl_format из разрешения + типа видео
        res_number = res.replace("p", "")
        if type == "video_with_audio":
            return (
                f"bestvideo[height<={res_number}]+bestaudio/best[height<={res_number}]"
            )
        elif type == "video_no_audio":
            return f"bestvideo[height<={res_number}]"
        elif type == "only_audio":
            return "bestaudio/best"

        return "best"

    async def _send_to_rabbitmq(self, download_task: dict):
        # Отправляет задачку в очередь RabbitMQ
        connection = await aio_pika.connect_robust(host=os.getenv("RABBITMQ_HOST"))
        async with connection:
            channel = await connection.channel()

            queue = await channel.declare_queue(os.getenv("QUEUE_NAME"), durable=True)

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(download_task).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue.name,
            )

    async def _show_download_started(self, chat_id: int, user_data: dict):
        # Показывает пользователю красивое сообщение
        type = user_data["video_type"]
        type_display = {
            "video_with_audio": "видео со звуком",
            "video_no_audio": "видео без звука",
            "only_audio": "только звук (MP3)",
        }.get(type, type)
        message_text = (
            f"Качество: {user_data['video_res']}\n"
            f"Тип видео: {type_display}\n"
            f"Ссылка на видео: {user_data['url']}\n"
            "Вы встали в очередь на загрузку...\n"
            "Пожалуйста, ожидайте..."
        )
        await bot.telegram_api_client.send_message(chat_id=chat_id, text=message_text)
