import bot.telegram_api_client
import bot.database_client
from bot.handlers.handler import Handler
from bot.types import STATE, STATUS


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
        await bot.database_client.update_user_state(telegram_id, STATE.WAIT_FOR_AUDIO)

        message_text = "Выбрано качество видео.\n Теперь выберите тип видео:\n"
        keyboard = [
            [{"text": "видео со звуком", "callback_data": "type_video_with_audio"}],
            [{"text": "видео без звука", "callback_data": "type_video_no_audio"}],
            [{"text": "только звук (MP3)", "callback_data": "type_only_audio"}],
        ]

        reply_markup = {"inline_keyboard": keyboard}

        await bot.telegram_api_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message_text,
            reply_markup=reply_markup,
        )

        await bot.telegram_api_client.answer_callback_query(callback_query["id"])
        return STATUS.STOP
