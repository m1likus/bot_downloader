import bot.database_client
import asyncio


async def main():
    await bot.database_client.delete_database()
    await bot.database_client.create_database()


if __name__ == "__main__":
    asyncio.run(main())
