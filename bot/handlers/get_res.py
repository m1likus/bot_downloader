import bot.telegram_api_client
import bot.database_client
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS
import asyncio
import yt_dlp
from bot.download_utils import DownloadUtils


class ResHandler(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return (
            "callback_query" in update
            and update["callback_query"]["data"].startswith("res_")
            and state == STATE.WAIT_FOR_RESOLUTION.value
        )

    async def handle(self, update: dict, state: STATE) -> STATUS:
        callback_query = update["callback_query"]
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        telegram_id = callback_query["from"]["id"]
        callback_data = callback_query["data"]
        resolution = callback_data.replace("res_", "")

        await bot.database_client.update_user_video_res(telegram_id, resolution)
        user_data = await bot.database_client.get_user(telegram_id)
        user_url = user_data["url"]
        avaliable_types = await self._check_available_types(user_url)

        types_map = {
            "video_with_audio": ("Видео со звуком", "type_video_with_audio"),
            "video_no_audio": ("Видео без звука", "type_video_no_audio"),
            "only_audio": ("Только звук", "type_only_audio"),
        }
        keyboard = []
        for key, (display_text, _callback_data) in types_map.items():
            if avaliable_types.get(key, False):
                keyboard.append(
                    [{"text": display_text, "callback_data": _callback_data}]
                )

        if len(keyboard) == 1:
            video_type = keyboard[0][0]["callback_data"].replace("type_", "")
            await self._start_download_process(
                telegram_id, chat_id, message_id, video_type
            )
            await bot.telegram_api_client.delete_message(chat_id, message_id)

        else:
            message_text = "Выбрано качество видео.\nТеперь выберите тип видео:\n"
            reply_markup = {"inline_keyboard": keyboard}
            await bot.database_client.update_user_state(
                telegram_id, STATE.WAIT_FOR_AUDIO
            )
            await bot.telegram_api_client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message_text,
                reply_markup=reply_markup,
            )
        await bot.telegram_api_client.answer_callback_query(callback_query["id"])
        return STATUS.STOP

    async def _check_available_types(self, url: str) -> dict:
        # Получает информацию о возможных типах видео
        loop = asyncio.get_event_loop()
        try:

            def _check():
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "skip_download": True,
                }
                available_types = {
                    "video_with_audio": False,
                    "video_no_audio": False,
                    "only_audio": False,
                }
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        formats = info.get("formats", [])
                        for format in formats:
                            vcodec = format.get("vcodec", "none")
                            acodec = format.get("acodec", "none")
                            flag = (vcodec != "none" and acodec != "none") or (
                                vcodec == "none" and acodec == "none"
                            )
                            if flag:
                                available_types["video_with_audio"] = True
                            elif vcodec != "none" and acodec == "none":
                                available_types["video_no_audio"] = True
                            elif vcodec == "none" and acodec != "none":
                                available_types["only_audio"] = True

                        return available_types
                except Exception:
                    return {
                        "video_with_audio": True,
                        "video_no_audio": False,
                        "only_audio": False,
                    }

            available_types = await loop.run_in_executor(None, _check)
            return available_types

        except Exception:
            return {
                "video_with_audio": True,
                "video_no_audio": False,
                "only_audio": False,
            }

    async def _start_download_process(
        self, telegram_id: int, chat_id: int, message_id: int, video_type: str
    ):
        # Запускает скачивание в том случае, если из доступных типов видео - только одно
        await bot.database_client.update_user_video_type(telegram_id, video_type)
        await bot.database_client.update_user_state(
            telegram_id, STATE.WAIT_FOR_START_DOWNLOADING
        )
        user_data = await bot.database_client.get_user(telegram_id)
        ydl_format = DownloadUtils._generate_ydl_format(
            user_data["video_res"], user_data["video_type"]
        )
        download_task = {
            "telegram_id": telegram_id,
            "chat_id": chat_id,
            "url": user_data["url"],
            "resolution": user_data["video_res"],
            "video_type": user_data["video_type"],
            "ydl_format": ydl_format,
        }
        try:
            await DownloadUtils._send_to_rabbitmq(download_task)
            await DownloadUtils._show_download_started(chat_id, user_data)
        except Exception:
            import traceback

            traceback.print_exc()
            await bot.database_client.clear_user_video_and_set_state(telegram_id)
            error_message = "Ошибка при запуске скачивания. Начните заново."
            await bot.telegram_api_client.send_message(
                chat_id=chat_id, text=error_message
            )
