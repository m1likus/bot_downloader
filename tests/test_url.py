from bot.dispatcher import Dispatcher
from bot.types import STATE, STATUS
from bot.handlers.url import UrlHandler
import bot
from tests.mocks import Mock
import pytest


@pytest.mark.asyncio
async def test_url_handler_can_handle_success_execution():
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
            "text": "https://vkvideo.ru/video837424820_456239073",
        },
    }

    url_handler = UrlHandler()
    result = url_handler.can_handle(test_update, STATE.WAIT_FOR_ID.value)
    assert result


@pytest.mark.asyncio
async def test_url_handler_can_handle_unsuccess_execution():
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
            "text": "https://vkvideo.ru/video837424820_456239073",
        },
    }

    url_handler = UrlHandler()
    result = url_handler.can_handle(test_update, STATE.WAIT_FOR_AUDIO)
    assert not result


@pytest.mark.asyncio
async def test_url_handler_cyrillic_text_execution():
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
            "text": "это кириллица",
        },
    }

    send_message_called = False
    message_text = ""

    async def get_user(telegram_id: int) -> dict:
        assert telegram_id == 12345
        return {
            "state": STATE.WAIT_FOR_ID.value,
            "url": "",
            "video_res": "",
            "video_type": "",
        }

    async def send_message(chat_id: int, text: str, **kwargs) -> dict:
        nonlocal send_message_called, message_text
        send_message_called = True
        message_text = text
        return {"ok": True}

    bot.database_client = Mock({"get_user": get_user})
    bot.telegram_api_client = Mock({"send_message": send_message})

    dispatcher = Dispatcher()
    url_handler = UrlHandler()
    dispatcher.add_handlers(url_handler)
    await dispatcher.dispatch(test_update)

    result = url_handler.can_handle(test_update, STATE.WAIT_FOR_ID.value)
    assert result
    assert send_message_called
    assert "Пожалуйста, введите ссылку или video-id" in message_text


@pytest.mark.asyncio
async def test_url_handler_invalid_url_execution():
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
            "text": "invalid",
        },
    }

    send_message_called = False
    message_text = ""

    async def get_user(telegram_id: int) -> dict:
        assert telegram_id == 12345
        return {"state": STATE.WAIT_FOR_ID.value}

    async def send_message(chat_id: int, text: str, **kwargs) -> dict:
        nonlocal send_message_called, message_text
        send_message_called = True
        message_text = text
        return {"ok": True}

    bot.database_client = Mock({"get_user": get_user})
    bot.telegram_api_client = Mock({"send_message": send_message})

    url_handler = UrlHandler()
    result = await url_handler.handle(test_update, STATE.WAIT_FOR_ID)

    assert result == STATUS.STOP
    assert send_message_called
    assert "Неверный формат" in message_text


@pytest.mark.asyncio
async def test_url_handler_video_unavailable_execution():
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
            "text": "https://vkvideo.ru/video123456789",
        },
    }

    send_message_called = False
    message_text = ""

    async def get_user(telegram_id: int) -> dict:
        assert telegram_id == 12345
        return {"state": STATE.WAIT_FOR_ID.value}

    async def send_message(chat_id: int, text: str, **kwargs) -> dict:
        nonlocal send_message_called, message_text
        send_message_called = True
        message_text = text
        return {"ok": True}

    async def validate_video(url: str) -> dict:
        return {"success": False, "error": "unavailable"}

    async def get_avaliable_res(url: str) -> dict:
        return []

    bot.database_client = Mock({"get_user": get_user})
    bot.telegram_api_client = Mock({"send_message": send_message})

    dispatcher = Dispatcher()
    url_handler = UrlHandler()

    url_handler._validate_video = validate_video
    url_handler._get_avaliable_resolutions = get_avaliable_res

    dispatcher.add_handlers(url_handler)
    await dispatcher.dispatch(test_update)

    assert send_message_called
    assert "Видео недоступно или было удалено" in message_text


@pytest.mark.asyncio
async def test_url_handler_video_success_validation_execution():
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
            "text": "https://vkvideo.ru/video123456789",
        },
    }

    update_user_video_called = False
    update_user_state_called = False
    send_message_called = False

    async def get_user(telegram_id: int) -> dict:
        assert telegram_id == 12345
        return {"state": STATE.WAIT_FOR_ID.value}

    async def update_user_video(telegram_id: int, url: str) -> None:
        nonlocal update_user_video_called
        update_user_video_called = True
        assert telegram_id == 12345
        assert url == "https://vkvideo.ru/video123456789"

    async def update_user_state(telegram_id: int, state: STATE) -> None:
        nonlocal update_user_state_called
        update_user_state_called = True
        assert telegram_id == 12345
        assert state == STATE.WAIT_FOR_RESOLUTION

    async def send_message(chat_id: int, text: str, **kwargs) -> dict:
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    async def validate_video(url: str) -> dict:
        return {
            "success": True,
            "title": "Test",
            "uploader": "Test",
            "duration": 100,
        }

    async def get_avaliable_res(url: str) -> dict:
        return ["1080p", "720p"]

    bot.database_client = Mock(
        {
            "get_user": get_user,
            "update_user_video": update_user_video,
            "update_user_state": update_user_state,
        }
    )
    bot.telegram_api_client = Mock({"send_message": send_message})

    dispatcher = Dispatcher()
    url_handler = UrlHandler()

    url_handler._validate_video = validate_video
    url_handler._get_avaliable_resolutions = get_avaliable_res

    dispatcher.add_handlers(url_handler)
    await dispatcher.dispatch(test_update)

    assert update_user_video_called
    assert update_user_state_called
    assert send_message_called
