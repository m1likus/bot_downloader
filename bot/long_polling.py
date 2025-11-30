from bot.dispatcher import Dispatcher
import bot.telegram_api_client


async def start_long_polling(dispatcher: Dispatcher) -> None:
    next_update_offset = 0
    while True:
        updates = await bot.telegram_api_client.get_updates(offset=next_update_offset)
        for update in updates:
            next_update_offset = max(next_update_offset, update["update_id"] + 1)
            await dispatcher.dispatch(update)
            try:
                telegram_id = update["message"]["from"]["id"]
            except Exception:
                telegram_id = update["callback_query"]["from"]["id"]
            print(f"Update from {telegram_id} \n", end="", flush=True)
