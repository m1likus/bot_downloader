from bot.dispatcher import Dispatcher
import bot.telegram_api_client
import time


def start_long_polling(dispatcher: Dispatcher) -> None:
    next_update_offset = 0
    while True:
        updates = bot.telegram_api_client.get_updates(offset=next_update_offset)
        for update in updates:
            next_update_offset = max(next_update_offset, update["update_id"] + 1)
            dispatcher.dispatch(update)
            telegram_id = update["message"]["from"]["id"]
            print(f"Update from {telegram_id} \n", end="", flush=True)
        time.sleep(1)
