import sqlite3
import os
import json
from bot.handlers.handler import STATE
from dotenv import load_dotenv

load_dotenv()


def create_database() -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                """
              CREATE TABLE IF NOT EXISTS telegram_updates
              (
                id INTEGER PRIMARY KEY
                payload TEXT NOT NULL
              )
              """,
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users
                (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER NOT NULL UNIQUE,
                state TEXT DEFAULT NULL,
                video_id TEXT DEFAULT NULL
                )
                """,
            )


def delete_database() -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute("DROP TABLE IF EXISTS telegram_updates")


def persist_updates(updates: dict) -> None:
    payload = json.dumps(updates, ensure_ascii=False, indent=2)
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.execute("INSERT INTO telegram updates (payload) VALUES (?)")


def ensure_user_exists(telegram_id: int) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            cursor = connection.execute(
                "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id)
            )
            if cursor.fetchone() is None:
                connection.execute(
                    "INSERT INTO users (telegram_id) VALUES (?)", (telegram_id)
                )


def clear_user_state_and_video(telegram_id: int) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET state = NULL, video_id = NULL WHERE telegram_id = ?",
                (telegram_id,),
            )


def update_user_state(telegram_id: int, state: STATE) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET state = ? WHERE telegram_id = ?", (state, telegram_id)
            )


def get_user(telegram_id: int) -> dict:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            cursor = connection.execute(
                "SELECT id, telegram_id, state, video_id FROM users WHERE telegram_id = ?",
                (telegram_id),
            )
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "telegram_id": result[1],
                    "state": result[2],
                    "video_id": result[3],
                }
            return None


def update_user_video(telegram_id: int, video: str) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET video_id = ? WHERE telegram_id = ?",
                (video, telegram_id),
            )
