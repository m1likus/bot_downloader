from bot.dispatcher import Dispatcher
from bot.handlers.message_start import MessageStart
import bot
import pytest
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_message_start_handler():
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "chat": {
                "id": 12345,
                "first_name": "Test",
                "username": "testuser",
                "type": "private",
            },
            "date": 1640995200,
            "text": "/start",
        },
    }

    clear_user_video_and_set_state_called = False
    send_message_called = False

    async def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 12345
        return {"state": None, "url": "", "video_res": "", "video_type": ""}

    async def clear_user_video_and_set_state(telegram_id: int) -> None:
        assert telegram_id == 12345
        nonlocal clear_user_video_and_set_state_called
        clear_user_video_and_set_state_called = True

    async def send_message(chat_id: int, text: str, **kwargs) -> dict:
        assert chat_id == 12345
        assert "Этот бот способен скачивать видео" in text
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_database_client = Mock(
        {
            "get_user": get_user,
            "clear_user_video_and_set_state": clear_user_video_and_set_state,
        }
    )

    mock_telegram_api_client = Mock({"send_message": send_message})
    bot.database_client = mock_database_client
    bot.telegram_api_client = mock_telegram_api_client

    dispatcher = Dispatcher()
    dispatcher.add_handlers(MessageStart())
    await dispatcher.dispatch(test_update)

    assert clear_user_video_and_set_state_called
    assert send_message_called
