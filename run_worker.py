from bot.worker import DownloadWorker
import asyncio


async def main():
    print("Starting download worker...")
    worker = DownloadWorker()
    try:
        await worker.start_consuming()
    except KeyboardInterrupt:
        print("\nWorker остановлен")


if __name__ == "__main__":
    asyncio.run(main())
