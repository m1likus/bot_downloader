import bot.telegram_api_client
import bot.database_client
import re
import yt_dlp
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS
import asyncio


class UrlHandler(Handler):
    def can_handle(self, update: dict, state: STATE) -> bool:
        return (
            "message" in update
            and "text" in update["message"]
            and state == (STATE.WAIT_FOR_ID.value)
        )

    async def handle(self, update: dict, state: STATE) -> STATUS:
        telegram_id = update["message"]["from"]["id"]
        text = update["message"]["text"].strip()
        chat_id = update["message"]["from"]["id"]

        cyrillic_pattern = re.compile("[\u0400-\u04ff]")
        if cyrillic_pattern.search(text):
            await bot.telegram_api_client.send_message(
                chat_id=chat_id,
                text="Пожалуйста, введите ссылку или video-id. Поддерживаемые платформы: \n"
                "YouTube\n"
                "VK Video \n"
                "Twitch \n"
                "etc.",
            )
            return STATUS.STOP

        processed_url = self._process_user_input(text)
        if not processed_url:
            await bot.telegram_api_client.send_message(
                chat_id=chat_id,
                text="Неверный формат. Введите ссылку на видео или video-id \n",
            )
            return STATUS.STOP

        validation_result = await self._validate_video(processed_url)
        if not validation_result["success"]:
            error_message = self._get_user_friendly_error(validation_result["error"])
            await bot.telegram_api_client.send_message(
                chat_id=chat_id, text=error_message
            )
            return STATUS.STOP

        await bot.database_client.update_user_video(telegram_id, text)
        await bot.database_client.update_user_state(
            telegram_id, STATE.WAIT_FOR_RESOLUTION
        )

        available_resolutions = await self._get_avaliable_resolutions(processed_url)
        message_text = (
            f"Видео найдено!\n"
            f"Название: {validation_result['title']}\n"
            f"Автор: {validation_result['uploader']}\n"
            f"Длительность: {self._format_duration(validation_result['duration'])}\n"
            f"Выберите качество видео: "
        )
        keyboard = []
        for res in available_resolutions:
            keyboard.append([{"text": f"{res}", "callback_data": f"res_{res}"}])

        reply_markup = {"inline_keyboard": keyboard}

        await bot.telegram_api_client.send_message(
            chat_id=chat_id, text=message_text, reply_markup=reply_markup
        )

        return STATUS.STOP

    def _process_user_input(self, input: str) -> str:
        # Обрабатывает ввод пользователя
        if self._is_video_id(input):
            return f"https://www.youtube.com/watch?v={input}"
        if self._is_url(input):
            return input
        return None

    def _is_video_id(self, text: str) -> bool:
        # Проверяет является ли текст video-id
        id_pattern = re.compile(r"^[a-zA-Z0-9_-]{11}")
        return bool(id_pattern.match(text))

    def _is_url(self, text: str) -> bool:
        # Проверяет является ли текст ссылкой
        url_patterns = [
            r"https?://",
            r"www\.",
            r"\.(com|org|net|ru|vk|tv|video|live|be)",
        ]
        for pattern in url_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    async def _validate_video(self, url: str) -> dict:
        # Валидирует видео через yt_dlp
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            loop = asyncio.get_event_loop()

            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)

            info = await loop.run_in_executor(None, extract_info)
            return {
                "success": True,
                "title": info.get("title", "Неизвестное название"),
                "uploader": info.get("uploader", "Неизвестный автор"),
                "duration": info.get("duration", 0),
            }

        except yt_dlp.utils.DownloadError as e:
            error_message = str(e)
            if "Private video" in error_message:
                return {"success": False, "error": "private"}
            elif "Video unavailable" in error_message:
                return {"success": False, "error": "unavailable"}
            elif "Sign in to confirm" in error_message:
                return {"success": False, "error": "age_restricted"}
            elif "Unsupported URL" in error_message:
                return {"success": False, "error": "unsupported_url"}
            else:
                return {"success": False, "error": "download_error"}
        except Exception as e:
            return {"success": False, "error": f"unexpected: {str(e)}"}

    def _get_user_friendly_error(self, error: str) -> str:
        # Возвращает пользователю понятное сообщение об ошибке
        error_messages = {
            "private": "Это видео является приватным и недоступно для скачивания",
            "unavailable": "Видео недоступно или было удалено.",
            "age_restricted": "Это видео имеет возрастные ограничения и недоступно.",
            "unsupported_url": "Данная ссылка не поддерживается.",
            "download_error": "Произошла ошибка при проверке видео.",
            "unexpected": "Неожиданная ошибка. Попробуйте позже.",
        }
        return error_messages.get(error, "Произошла неизвестная ошибка")

    async def _get_avaliable_resolutions(self, url: str) -> list:
        # Из yt_dlp получаем возможные разрешения для данного видео
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        try:
            loop = asyncio.get_event_loop()

            def extract_formats():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get("formats", [])

            formats = await loop.run_in_executor(None, extract_formats)
            resolutions = set()
            for format in formats:
                if format.get("height"):
                    resolution = f"{format['height']}p"
                    resolutions.add(resolution)

            sorted_res = sorted(
                resolutions, key=lambda x: int(x.replace("p", "")), reverse=True
            )
            return sorted_res[:5]
        except Exception:
            return []

    def _format_duration(self, seconds: int) -> str:
        # Форматирует длительность видео в понятный пользователю вид
        if not seconds:
            return "0"

        hours = seconds // 3600
        seconds = seconds % 3600
        minutes = seconds // 60
        seconds = seconds % 60

        return f"{hours}:{minutes:02d}:{seconds:02d}"
