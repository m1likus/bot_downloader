import json
import yt_dlp
import os
import traceback
import aio_pika
import asyncio
import bot.telegram_api_client
import bot.database_client
from bot.types import STATE


class DownloadWorker:
    async def start_consuming(self):
        try:
            connection = await aio_pika.connect_robust(host=os.getenv("RABBITMQ_HOST"))
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)

                queue = await channel.declare_queue(
                    os.getenv("QUEUE_NAME"), durable=True
                )
                print("Worker запущен и слушает очередь...")

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            try:
                                download_task = json.loads(message.body.decode())
                                telegram_id = download_task["telegram_id"]
                                await self.process_download_task(download_task)
                            except Exception:
                                traceback.print_exc()
                                chat_id = download_task["chat_id"]
                                if telegram_id:
                                    await bot.database_client.clear_user_video_and_set_state(
                                        telegram_id
                                    )
                                if chat_id:
                                    await bot.telegram_api_client.send_message(
                                        chat_id=chat_id,
                                        text="Ошибка при скачивании. Попробуйте еще раз.",
                                    )
        except Exception as e:
            print(f"Ошибка при запуске воркера: {e}")
            traceback.print_exc()

    async def process_download_task(self, task: dict):
        telegram_id = task["telegram_id"]
        chat_id = task["chat_id"]
        url = task["url"]
        ydl_format = task["ydl_format"]

        try:
            await bot.database_client.update_user_state(
                telegram_id, STATE.WAIT_FOR_DOWNLOAD
            )
            success = await self._download_and_send_file(
                chat_id, telegram_id, url, ydl_format
            )
            await bot.database_client.clear_user_video_and_set_state(telegram_id)

            if not success:
                await bot.telegram_api_client.send_message(
                    chat_id=chat_id,
                    text="Ошибка отправки. Попробуйте начать заново.",
                )

        except Exception:
            await bot.database_client.clear_user_video_and_set_state(telegram_id)
            await bot.telegram_api_client.send_message(
                chat_id=chat_id,
                text="Ошибка отправки. Попробуйте начать заново.",
            )

    async def _download_and_send_file(
        self, chat_id: int, telegram_id: int, url: str, ydl_format: str
    ) -> bool:
        loop = asyncio.get_event_loop()
        try:
            video_dir = "videos"
            os.makedirs(video_dir, exist_ok=True)

            def _download():
                ydl_opts = {
                    "format": ydl_format,
                    "outtmpl": os.path.join(video_dir, "%(title)s.%(ext)s"),
                    "quiet": False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info)
                    return file_path, info.get("title", "video")

            file_path, title = await loop.run_in_executor(None, _download)
            if not os.path.exists(file_path):
                print(f"Файл не найден: {file_path}")
                return False

            success = await bot.telegram_api_client.send_document(
                chat_id, file_path, title
            )
            try:
                os.remove(file_path)
            except Exception:
                pass

            return success

        except Exception as e:
            await bot.database_client.clear_user_video_and_set_state(telegram_id)
            print(f"Ошибка в _download_and_send_file: {e}")
            return False
