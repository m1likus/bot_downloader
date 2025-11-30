from bot.dispatcher import Dispatcher
from bot.types import STATE, STATUS
from bot.handlers.download import DownloadHandler
import bot
import pytest

from tests.mocks import Mock


@pytest.mark.asyncio
async def test_type_handler_can_handle_success_execution():
    test_update = {
        "update_id": 123456789,
        "callback_query": {
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "data": "type_video_with_audio",
            "message": {"chat": {"id": 12345}, "message_id": 1},
        },
    }

    type_handler = DownloadHandler()
    result = type_handler.can_handle(test_update, STATE.WAIT_FOR_AUDIO.value)
    assert result


@pytest.mark.asyncio
async def test_type_handler_can_handle_unsuccess_execution():
    test_update = {
        "update_id": 123456789,
        "callback_query": {
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "data": "type_video_with_audio",
            "message": {"chat": {"id": 12345}, "message_id": 1},
        },
    }

    async def get_user(telegram_id: int) -> dict:
        assert telegram_id == 12345
        return {
            "state": STATE.WAIT_FOR_ID.value,
            "url": "",
            "video_res": "",
            "video_type": "",
        }

    bot.database_client = Mock({"get_user": get_user})

    type_handler = DownloadHandler()
    result = type_handler.can_handle(test_update, STATE.WAIT_FOR_AUDIO)
    assert not result


@pytest.mark.asyncio
async def test_download_handler_handle_success_execution():
    test_update = {
        "update_id": 123456789,
        "callback_query": {
            "id": "callback123",
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "data": "type_video_with_audio",
            "message": {"chat": {"id": 12345}, "message_id": 1},
        },
    }

    update_user_video_type_called = False
    update_user_state_called = False
    get_user_called = False
    delete_message_called = False
    answer_callback_query_called = False
    send_message_called = False

    type_set = ""
    state_set = None
    chat_id_deleted = 0
    message_id_deleted = 0
    callback_id = ""
    message_text = ""

    async def get_user(telegram_id: int) -> dict:
        nonlocal get_user_called
        get_user_called = True
        assert telegram_id == 12345
        return {
            "state": STATE.WAIT_FOR_RESOLUTION.value,
            "url": "https://vkvideo.ru/video837424820_456239073",
            "video_res": "720p",
            "video_type": "video_with_audio",
        }

    async def update_user_video_type(telegram_id: int, video_type: str) -> None:
        nonlocal update_user_video_type_called, type_set
        update_user_video_type_called = True
        assert telegram_id == 12345
        type_set = video_type

    async def update_user_state(telegram_id: int, state: STATE) -> None:
        nonlocal update_user_state_called, state_set
        update_user_state_called = True
        assert telegram_id == 12345
        state_set = state

    async def delete_message(chat_id: int, message_id: int) -> dict:
        nonlocal delete_message_called, chat_id_deleted, message_id_deleted
        delete_message_called = True
        chat_id_deleted = chat_id
        message_id_deleted = message_id
        return {"ok": True}

    async def answer_callback_query(callback_query_id: str) -> dict:
        nonlocal answer_callback_query_called, callback_id
        answer_callback_query_called = True
        callback_id = callback_query_id
        return {"ok": True}

    async def send_message(chat_id: int, text: str) -> dict:
        nonlocal send_message_called, message_text
        send_message_called = True
        message_text = text
        return {"ok": True}

    async def send_to_rabbitmq(task):
        return None

    bot.database_client = Mock(
        {
            "get_user": get_user,
            "update_user_video_type": update_user_video_type,
            "update_user_state": update_user_state,
        }
    )
    bot.telegram_api_client = Mock(
        {
            "delete_message": delete_message,
            "answer_callback_query": answer_callback_query,
            "send_message": send_message,
        }
    )

    dispatcher = Dispatcher()
    type_handler = DownloadHandler()

    type_handler._send_to_rabbitmq = send_to_rabbitmq
    dispatcher.add_handlers(type_handler)
    await dispatcher.dispatch(test_update)
    result = await type_handler.handle(test_update, STATE.WAIT_FOR_AUDIO)

    assert result == STATUS.STOP

    assert update_user_video_type_called
    assert type_set == "video_with_audio"

    assert update_user_state_called
    assert state_set == STATE.WAIT_FOR_START_DOWNLOADING

    assert get_user_called
    assert delete_message_called
    assert chat_id_deleted == 12345
    assert message_id_deleted == 1

    assert answer_callback_query_called
    assert callback_id == "callback123"

    assert send_message_called
    assert "Вы встали в очередь на загрузку" in message_text
