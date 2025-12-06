import os
import json
import aio_pika
import bot.telegram_api_client


class DownloadUtils:
    @staticmethod
    def _generate_ydl_format(res: str, type: str) -> str:
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

    @staticmethod
    async def _send_to_rabbitmq(download_task: dict):
        # Отправляет задачку в очередь RabbitMQ
        connection = await aio_pika.connect_robust(host=os.getenv("RABBITMQ_HOST"))
        async with connection:
            channel = await connection.channel()

            queue = await channel.declare_queue(
                os.getenv("RABBITMQ_QUEUE_NAME"), durable=True
            )

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(download_task).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue.name,
            )

    @staticmethod
    async def _show_download_started(chat_id: int, user_data: dict):
        # Показывает пользователю красивое сообщение
        type = user_data["video_type"]
        type_display = {
            "video_with_audio": "Видео со звуком",
            "video_no_audio": "Видео без звука",
            "only_audio": "Только звук",
        }.get(type, type)
        message_text = (
            f"Качество: {user_data['video_res']}\n"
            f"Тип видео: {type_display}\n"
            f"Ссылка на видео: {user_data['url']}\n"
            "Вы встали в очередь на загрузку...\n"
            "Пожалуйста, ожидайте..."
        )
        await bot.telegram_api_client.send_message(chat_id=chat_id, text=message_text)
