import os
import json
from bot.types import STATE
from dotenv import load_dotenv
import asyncpg

load_dotenv()

_pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DATABASE")

        if host is None:
            raise ValueError("POSTGRES_HOST environment variable is not set")
        if port is None:
            raise ValueError("POSTGRES_PORT environment variable is not set")
        if user is None:
            raise ValueError("POSTGRES_USER environment variable is not set")
        if password is None:
            raise ValueError("POSTGRES_PASSWORD environment variable is not set")
        if database is None:
            raise ValueError("POSTGRES_DATABASE environment variable is not set")

        _pool = await asyncpg.create_pool(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            min_size=1,
            max_size=10,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def create_database() -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_updates
            (
                id SERIAL PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """,
        )
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users
            (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            state TEXT DEFAULT NULL,
            url TEXT DEFAULT NULL,
            video_res TEXT DEFAULT NULL,
            video_type TEXT DEFAULT NULL
            )
            """,
        )


async def delete_database() -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute("DROP TABLE IF EXISTS telegram_updates")
            await connection.execute("DROP TABLE IF EXISTS users")


async def persist_updates(updates: dict) -> None:
    payload = json.dumps(updates, ensure_ascii=False, indent=2)
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "INSERT INTO telegram_updates (payload) VALUES ($1)", payload
            )


async def ensure_user_exists(telegram_id: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow(
                "SELECT 1 FROM users WHERE telegram_id = $1",
                telegram_id,
            )
            if result is None:
                await connection.execute(
                    "INSERT INTO users (telegram_id) VALUES ($1)",
                    telegram_id,
                )


async def clear_user_video_and_set_state(telegram_id: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE users SET state = $1, url = NULL, video_res = NULL, video_type = NULL WHERE telegram_id = $2",
                STATE.WAIT_FOR_ID.value,
                telegram_id,
            )


async def update_user_state(telegram_id: int, state: STATE) -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE users SET state = $1 WHERE telegram_id = $2",
                state.value,
                telegram_id,
            )


async def get_user(telegram_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow(
                "SELECT id, telegram_id, state, url, video_res, video_type FROM users WHERE telegram_id = $1",
                telegram_id,
            )
            if result:
                return {
                    "id": result[0],
                    "telegram_id": result[1],
                    "state": result[2],
                    "url": result[3],
                    "video_res": result[4],
                    "video_type": result[5],
                }
            return None


async def update_user_video(telegram_id: int, video: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE users SET url = $1 WHERE telegram_id = $2",
                video,
                telegram_id,
            )


async def update_user_video_res(telegram_id: int, video_res: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE users SET video_res = $1 WHERE telegram_id = $2",
                video_res,
                telegram_id,
            )


async def update_user_video_type(telegram_id: int, video_type: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE users SET video_type = $1 WHERE telegram_id = $2",
                video_type,
                telegram_id,
            )
