import bot.long_polling
from bot.dispatcher import Dispatcher
from bot.handlers import get_handlers


def main() -> None:
    try:
        dispatcher = Dispatcher()
        dispatcher.add_handlers(*get_handlers())
        bot.long_polling.start_long_polling(dispatcher)
    except KeyboardInterrupt:
        print("\nBot stopped working.")


if __name__ == "__main__":
    main()
