from bot.worker import DownloadWorker
from bot.types import STATE
import yt_dlp
import bot
import os
import pytest

from tests.mocks import Mock


@pytest.mark.asyncio
async def test_process_download_task_success_execution():
    task = {
        "telegram_id": 12345,
        "chat_id": 12345,
        "url": "https://vkvideo.ru/video837424820_456239073",
        "ydl_format": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    }

    update_user_state_called = False
    clear_user_state_called = False
    send_document_called = False
    send_message_called = False

    state_set = None
    telegram_id_cleared = 0
    file_path_sent = ""
    title_sent = ""

    async def update_user_state(telegram_id: int, state: STATE) -> None:
        nonlocal update_user_state_called, state_set
        update_user_state_called = True
        assert telegram_id == 12345
        state_set = state

    async def clear_user_state_and_video(telegram_id: int) -> None:
        nonlocal clear_user_state_called, telegram_id_cleared
        clear_user_state_called = True
        telegram_id_cleared = telegram_id

    async def send_document(chat_id: int, file_path: str, title: str) -> bool:
        nonlocal send_document_called, file_path_sent, title_sent
        send_document_called = True
        file_path_sent = file_path
        title_sent = title
        return True

    async def send_message(chat_id: int, text: str) -> None:
        nonlocal send_message_called
        send_message_called = True

    bot.database_client = Mock(
        {
            "update_user_state": update_user_state,
            "clear_user_state_and_video": clear_user_state_and_video,
        }
    )
    bot.telegram_api_client = Mock(
        {"send_document": send_document, "send_message": send_message}
    )

    class MockYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def extract_info(self, url, download=True):
            return {"title": "Test", "ext": "mp4"}

        def prepare_filename(self, info):
            return "/tmp/test.mp4"

    yt_dlp.YoutubeDL = MockYoutubeDL

    async def process_download_task(task: dict):
        telegram_id = task["telegram_id"]
        chat_id = task["chat_id"]

        await bot.database_client.update_user_state(
            telegram_id, STATE.WAIT_FOR_DOWNLOAD
        )

        url = "https://vkvideo.ru/video837424820_456239073"
        ydl_format = "bestvideo[height<=360]+bestaudio/best[height<=360]"
        success = await worker._download_and_send_file(
            chat_id, telegram_id, url, ydl_format
        )

        await bot.database_client.clear_user_state_and_video(telegram_id)
        if not success:
            await bot.telegram_api_client.send_message(
                chat_id=chat_id,
                text="Ошибка отправки. Попробуйте начать заново.",
            )

    os.path.exists = lambda path: True

    worker = DownloadWorker()

    worker.process_download_task = process_download_task
    await worker.process_download_task(task)

    assert update_user_state_called
    assert state_set == STATE.WAIT_FOR_DOWNLOAD
    assert clear_user_state_called
    assert telegram_id_cleared == 12345
    assert send_document_called
    assert file_path_sent == "/tmp/test.mp4"
    assert title_sent == "Test"
