import urllib.request
import json
import os
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class METHODS(Enum):
    getMe = "getMe"
    getUpdates = "getUpdates"
    sendMessage = "sendMessage"
    sendDocument = "sendDocument"
    deleteMessage = "deleteMessage"
    editMessageText = "editMessageText"


def make_request(method: METHODS, **args) -> dict:
    json_data = json.dumps(args).encode("utf-8")

    request = urllib.request.Request(
        method="POST",
        url=f"{os.getenv('TELEGRAM_BASE_URI')}/{method}",
        data=json_data,
        headers={
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
        response_json = json.loads(response_body)
        assert response_json["ok"] == True
        return response_json["result"]


def get_me() -> dict:
    return make_request(METHODS.getMe)


def get_updates(**args) -> dict:
    # https://core.telegram.org/bots/api#getupdates
    return make_request(METHODS.getUpdates, **args)


def send_message(chat_id: int, text: str, **args) -> dict:
    # https://core.telegram.org/bots/api#sendmessage
    return make_request(METHODS.sendMessage, chat_id=chat_id, text=text, **args)


def send_document(chat_id: int, video: str, **args) -> dict:
    # https://core.telegram.org/bots/api#senddocument
    return make_request(METHODS.sendDocument, chat_id=chat_id, video=video, **args)


def delete_message(chat_id: int, message_id: int) -> dict:
    # https://core.telegram.org/bots/api#deletemessage
    return make_request(METHODS.deleteMessage, chat_id=chat_id, message_id=message_id)


def edit_message_text(chat_id: int, message_id: int, text: str) -> dict:
    # https://core.telegram.org/bots/api#editmessagetext
    return make_request(
        METHODS.editMessageText, chat_id=chat_id, message_id=message_id, text=text
    )
