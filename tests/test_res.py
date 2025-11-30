from bot.dispatcher import Dispatcher
from bot.types import STATE
from bot.handlers.get_res import ResHandler
import bot
import pytest

from tests.mocks import Mock


@pytest.mark.asyncio
async def test_res_handler_can_handle_success_execution():
    test_update = {
        "update_id": 123456789,
        "callback_query": {
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "data": "res_720p",
        },
    }

    res_handler = ResHandler()
    result = res_handler.can_handle(test_update, STATE.WAIT_FOR_RESOLUTION.value)
    assert result


@pytest.mark.asyncio
async def test_res_handler_can_handle_unsuccess_execution():
    test_update = {
        "update_id": 123456789,
        "callback_query": {
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "data": "res_720p",
        },
    }

    res_handler = ResHandler()
    result = res_handler.can_handle(test_update, STATE.WAIT_FOR_AUDIO.value)
    assert not result


@pytest.mark.asyncio
async def test_res_handler_can_handle_no_callback_query_execution():
    test_update = {"message": {"from": {"id": 12345}, "text": "some text"}}

    res_handler = ResHandler()
    result = res_handler.can_handle(test_update, STATE.WAIT_FOR_RESOLUTION.value)

    assert not result


@pytest.mark.asyncio
async def test_res_handler_handle_success_execution():
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
            "data": "res_720p",
            "message": {"chat": {"id": 12345}, "message_id": 1},
        },
    }

    update_user_video_res_called = False
    update_user_state_called = False
    edit_message_text_called = False
    answer_callback_query_called = False

    resolution_set = ""
    state_set = None
    message_text = ""
    callback_id = ""

    async def get_user(telegram_id: int) -> dict:
        assert telegram_id == 12345
        return {
            "state": STATE.WAIT_FOR_RESOLUTION.value,
            "url": "https://vkvideo.ru/video837424820_456239073",
            "video_res": "",
            "video_type": "",
        }

    async def update_user_video_res(telegram_id: int, resolution: str) -> None:
        nonlocal update_user_video_res_called, resolution_set
        update_user_video_res_called = True
        assert telegram_id == 12345
        resolution_set = resolution

    async def update_user_state(telegram_id: int, state: STATE) -> None:
        nonlocal update_user_state_called, state_set
        update_user_state_called = True
        assert telegram_id == 12345
        state_set = state

    async def edit_message_text(
        chat_id: int, message_id: int, text: str, reply_markup: dict
    ) -> dict:
        nonlocal edit_message_text_called, message_text
        edit_message_text_called = True
        assert chat_id == 12345
        assert message_id == 1
        message_text = text
        assert "inline_keyboard" in reply_markup
        return {"ok": True}

    async def answer_callback_query(callback_query_id: str) -> dict:
        nonlocal answer_callback_query_called, callback_id
        answer_callback_query_called = True
        callback_id = callback_query_id
        return {"ok": True}

    bot.database_client = Mock(
        {
            "get_user": get_user,
            "update_user_video_res": update_user_video_res,
            "update_user_state": update_user_state,
        }
    )
    bot.telegram_api_client = Mock(
        {
            "edit_message_text": edit_message_text,
            "answer_callback_query": answer_callback_query,
        }
    )

    dispatcher = Dispatcher()
    res_handler = ResHandler()
    dispatcher.add_handlers(res_handler)
    await dispatcher.dispatch(test_update)

    assert update_user_video_res_called
    assert resolution_set == "720p"

    assert update_user_state_called
    assert state_set == STATE.WAIT_FOR_AUDIO

    assert edit_message_text_called
    assert "Выбрано качество видео" in message_text

    assert answer_callback_query_called
    assert callback_id == "callback123"
