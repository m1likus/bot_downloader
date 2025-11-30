import json
import os
from enum import Enum
from dotenv import load_dotenv
import aiohttp
import aiofiles

load_dotenv()


class METHODS(Enum):
    getMe = "getMe"
    getUpdates = "getUpdates"
    sendMessage = "sendMessage"
    deleteMessage = "deleteMessage"
    editMessageText = "editMessageText"
    answerCallbackQuery = "answerCallbackQuery"


async def make_request(method: METHODS, **args) -> dict:
    json_data = json.dumps(args).encode("utf-8")
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/{method.value}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            data=json_data,
            headers={
                "Content-Type": "application/json",
            },
        ) as response:
            response_body = await response.text()
            response_json = json.loads(response_body)
            assert response_json["ok"]
            return response_json["result"]


async def get_me() -> dict:
    return await make_request(METHODS.getMe)


async def get_updates(**kwargs) -> dict:
    # https://core.telegram.org/bots/api#getupdates
    return await make_request(METHODS.getUpdates, **kwargs)


async def send_message(chat_id: int, text: str, **kwargs) -> dict:
    # https://core.telegram.org/bots/api#sendmessage
    return await make_request(METHODS.sendMessage, chat_id=chat_id, text=text, **kwargs)


async def send_document(chat_id: int, document_path: str, caption: str = "") -> dict:
    # https://core.telegram.org/bots/api#senddocument
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendDocument"
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(document_path, "rb") as file:
            file_data = await file.read()
            form_data = aiohttp.FormData()
            form_data.add_field(
                "document", file_data, filename=os.path.basename(document_path)
            )
            form_data.add_field("chat_id", str(chat_id))
            form_data.add_field("caption", caption)

            async with session.post(url, data=form_data) as response:
                response_json = await response.json()
                return response_json["ok"]


async def delete_message(chat_id: int, message_id: int, **kwargs) -> dict:
    # https://core.telegram.org/bots/api#deletemessage
    return await make_request(
        METHODS.deleteMessage,
        chat_id=chat_id,
        message_id=message_id,
        **kwargs,
    )


async def edit_message_text(chat_id: int, message_id: int, text: str, **kwargs) -> dict:
    # https://core.telegram.org/bots/api#editmessagetext
    return await make_request(
        METHODS.editMessageText,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        **kwargs,
    )


async def answer_callback_query(callback_query_id: str, **kwargs) -> dict:
    # https://core.telegram.org/bots/api#answercallbackquery
    return await make_request(
        METHODS.answerCallbackQuery,
        callback_query_id=callback_query_id,
        **kwargs,
    )
