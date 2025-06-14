import psycopg2
from psycopg2.extras import DictCursor
from typing import Optional, List, Dict, Any
from config import db_config
import os
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(**db_config)

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    user_id BIGINT,
                    template_name TEXT,
                    template_text TEXT,
                    category TEXT DEFAULT 'без категории',
                    PRIMARY KEY (user_id, template_name)
                );
                CREATE TABLE IF NOT EXISTS speed_servers (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    url TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS voice_messages (
                    user_id BIGINT,
                    voice_name TEXT,
                    file_path TEXT,
                    category TEXT DEFAULT 'без категории',
                    PRIMARY KEY (user_id, voice_name)
                );
                CREATE TABLE IF NOT EXISTS animations (
                    user_id BIGINT,
                    anim_name TEXT,
                    frames TEXT,
                    PRIMARY KEY (user_id, anim_name)
                );
                CREATE TABLE IF NOT EXISTS video_notes (
                    user_id BIGINT,
                    video_note_name TEXT,
                    file_path TEXT,
                    PRIMARY KEY (user_id, video_note_name)
                );
                CREATE TABLE IF NOT EXISTS fake_activities (
                    user_id BIGINT,
                    chat_id BIGINT,
                    activity_type TEXT,
                    PRIMARY KEY (user_id, chat_id, activity_type)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    user_id BIGINT PRIMARY KEY,
                    prefix TEXT NOT NULL DEFAULT '.',
                    edit_text TEXT DEFAULT '🫥🫥🫥',
                    delete_cmd TEXT DEFAULT 'дд'
                );
                CREATE TABLE IF NOT EXISTS aliases (
                    user_id BIGINT NOT NULL,
                    alias_name TEXT,
                    command TEXT NOT NULL,
                    PRIMARY KEY (user_id, alias_name)
                );
                CREATE TABLE IF NOT EXISTS intervals (
                    user_id BIGINT,
                    interval_name TEXT,
                    chat_id BIGINT,
                    interval_minutes INTEGER,
                    interval_text TEXT,
                    PRIMARY KEY (user_id, interval_name)
                );
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"DB Init Error: {e}")
    finally:
        conn.close()

async def template_exists(user_id: int, template_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM templates WHERE user_id = %s AND template_name = %s",
                (user_id, template_name)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"DB Error in template_exists: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_template(user_id: int, template_name: str, template_text: str, category: str = "без категории") -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO templates (user_id, template_name, template_text, category) VALUES (%s, %s, %s, %s)",
                (user_id, template_name, template_text, category)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error in save_template: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def get_template(user_id: int, template_name: str) -> Optional[Tuple[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT template_text, category FROM templates WHERE user_id = %s AND template_name = %s",
                (user_id, template_name)
            )
            result = cursor.fetchone()
            return (result[0], result[1]) if result else None
    except Exception as e:
        logger.error(f"DB Error in get_template: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def delete_template(user_id: int, template_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM templates WHERE user_id = %s AND template_name = %s",
                (user_id, template_name)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error in delete_template: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_templates(user_id: int, category: Optional[str] = None) -> List[Tuple[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if category:
                cursor.execute(
                    "SELECT template_name, category FROM templates WHERE user_id = %s AND category = %s ORDER BY template_name",
                    (user_id, category)
                )
            else:
                cursor.execute(
                    "SELECT template_name, category FROM templates WHERE user_id = %s ORDER BY template_name",
                    (user_id,)
                )
            return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error in list_templates: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def list_categories(user_id: int) -> List[Tuple[str, int]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM templates
                WHERE user_id = %s
                GROUP BY category
                ORDER BY category
                """,
                (user_id,)
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error in list_categories: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def add_speed_server(name: str, url: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO speed_servers (name, url) VALUES (%s, %s)",
                (name, url)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def remove_speed_server(name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM speed_servers WHERE name = %s",
                (name,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_speed_servers() -> List[Dict[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, url FROM speed_servers ORDER BY id"
            )
            return [{"id": row[0], "name": row[1], "url": row[2]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def get_speed_server(server_id: int) -> Optional[Dict[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT name, url FROM speed_servers WHERE id = %s",
                (server_id,)
            )
            result = cursor.fetchone()
            return {"name": result[0], "url": result[1]} if result else None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def voice_message_exists(user_id: int, voice_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM voice_messages WHERE user_id = %s AND voice_name = %s",
                (user_id, voice_name)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_voice_message(user_id: int, voice_name: str, file_path: str, category: str = "без категории") -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO voice_messages (user_id, voice_name, file_path, category) VALUES (%s, %s, %s, %s)",
                (user_id, voice_name, file_path, category)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error in save_voice_message: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def delete_voice_message(user_id: int, voice_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_path FROM voice_messages WHERE user_id = %s AND voice_name = %s",
                (user_id, voice_name)
            )
            result = cursor.fetchone()
            if result:
                file_path = result[0]
                cursor.execute(
                    "DELETE FROM voice_messages WHERE user_id = %s AND voice_name = %s",
                    (user_id, voice_name)
                )
                conn.commit()
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
            return False
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_voice_messages(user_id: int, category: Optional[str] = None) -> List[Dict[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if category:
                cursor.execute(
                    "SELECT voice_name, category FROM voice_messages WHERE user_id = %s AND category = %s ORDER BY voice_name",
                    (user_id, category)
                )
            else:
                cursor.execute(
                    "SELECT voice_name, category FROM voice_messages WHERE user_id = %s ORDER BY voice_name",
                    (user_id,)
                )
            return [{"name": row[0], "category": row[1]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error in list_voice_messages: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def get_voice_message(user_id: int, voice_name: str) -> Optional[Dict[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_path, category FROM voice_messages WHERE user_id = %s AND voice_name = %s",
                (user_id, voice_name)
            )
            result = cursor.fetchone()
            return {"file_path": result[0], "category": result[1]} if result else None
    except Exception as e:
        logger.error(f"DB Error in get_voice_message: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def list_voice_categories(user_id: int) -> List[Tuple[str, int]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM voice_messages
                WHERE user_id = %s
                GROUP BY category
                ORDER BY category
                """,
                (user_id,)
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error in list_voice_categories: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def anim_exists(user_id: int, anim_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM animations WHERE user_id = %s AND anim_name = %s",
                (user_id, anim_name)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_animation(user_id: int, anim_name: str, frames: List[str]) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            frames_str = " #$ ".join(frames)
            cursor.execute(
                "INSERT INTO animations (user_id, anim_name, frames) VALUES (%s, %s, %s)",
                (user_id, anim_name, frames_str)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def delete_animation(user_id: int, anim_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM animations WHERE user_id = %s AND anim_name = %s",
                (user_id, anim_name)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def get_animation(user_id: int, anim_name: str) -> Optional[List[str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT frames FROM animations WHERE user_id = %s AND anim_name = %s",
                (user_id, anim_name)
            )
            result = cursor.fetchone()
            if result:
                return [frame.strip() for frame in result[0].split("#$") if frame.strip()]
            return None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def list_animations(user_id: int) -> List[str]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT anim_name FROM animations WHERE user_id = %s ORDER BY anim_name",
                (user_id,)
            )
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def video_note_exists(user_id: int, video_note_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM video_notes WHERE user_id = %s AND video_note_name = %s",
                (user_id, video_note_name)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_video_note(user_id: int, video_note_name: str, file_path: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO video_notes (user_id, video_note_name, file_path) VALUES (%s, %s, %s)",
                (user_id, video_note_name, file_path)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def delete_video_note(user_id: int, video_note_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_path FROM video_notes WHERE user_id = %s AND video_note_name = %s",
                (user_id, video_note_name)
            )
            result = cursor.fetchone()
            if result:
                file_path = result[0]
                cursor.execute(
                    "DELETE FROM video_notes WHERE user_id = %s AND video_note_name = %s",
                    (user_id, video_note_name)
                )
                conn.commit()
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
            return False
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_video_notes(user_id: int) -> List[Dict[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT video_note_name, file_path FROM video_notes WHERE user_id = %s ORDER BY video_note_name",
                (user_id,)
            )
            return [{"name": row[0], "file_path": row[1]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def get_video_note(user_id: int, video_note_name: str) -> Optional[str]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_path FROM video_notes WHERE user_id = %s AND video_note_name = %s",
                (user_id, video_note_name)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def add_fake_activity(user_id: int, chat_id: int, activity_type: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO fake_activities (user_id, chat_id, activity_type) VALUES (%s, %s, %s)",
                (user_id, chat_id, activity_type)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def remove_fake_activity(user_id: int, chat_id: int, activity_type: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM fake_activities WHERE user_id = %s AND chat_id = %s AND activity_type = %s",
                (user_id, chat_id, activity_type)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_fake_activities(user_id: int, activity_type: str) -> List[Dict[str, int]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT chat_id FROM fake_activities WHERE user_id = %s AND activity_type = %s ORDER BY chat_id",
                (user_id, activity_type)
            )
            return [{"chat_id": row[0]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def set_user_prefix(user_id: int, prefix: str) -> bool:
    """Устанавливает префикс для пользователя."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO settings (user_id, prefix) VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET prefix = %s
                """,
                (user_id, prefix, prefix)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка установки префикса: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def get_user_prefix(user_id: int) -> str:
    """Получает префикс пользователя или возвращает '.' по умолчанию."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT prefix FROM settings WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else "."
    except Exception as e:
        logger.error(f"Ошибка получения префикса: {e}")
        return "."
    finally:
        if conn:
            conn.close()

async def alias_exists(user_id: int, alias_name: str) -> bool:
    """Проверяет, существует ли алиас."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM aliases WHERE user_id = %s AND alias_name = %s",
                (user_id, alias_name)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_alias(user_id: int, alias_name: str, command: str) -> bool:
    """Сохраняет алиас в базу."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO aliases (user_id, alias_name, command) VALUES (%s, %s, %s)",
                (user_id, alias_name, command)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def delete_alias(user_id: int, alias_name: str) -> bool:
    """Удаляет алиас."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM aliases WHERE user_id = %s AND alias_name = %s",
                (user_id, alias_name)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_aliases(user_id: int) -> List[Dict[str, str]]:
    """Возвращает список алиасов пользователя."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT alias_name, command FROM aliases WHERE user_id = %s ORDER BY alias_name",
                (user_id,)
            )
            return [{"name": row[0], "command": row[1]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def get_alias_command(user_id: int, alias_name: str) -> Optional[str]:
    """Получает команду, связанную с алиасом."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT command FROM aliases WHERE user_id = %s AND alias_name = %s",
                (user_id, alias_name)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

async def get_edit_text(user_id: int) -> str:
    """Получает текст редактирования для пользователя."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT edit_text FROM settings WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result['edit_text'] if result else '🫥🫥🫥'
    except Exception as e:
        logger.error(f"Ошибка при получении edit_text для user_id={user_id}: {e}")
        return '🫥🫥🫥'
    finally:
        if conn:
            conn.close()

async def set_edit_text(user_id: int, edit_text: str) -> bool:
    """Устанавливает текст редактирования для пользователя."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO settings (user_id, edit_text)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET edit_text = %s
            """, (user_id, edit_text, edit_text))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при установке edit_text для user_id={user_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def get_delete_cmd(user_id: int) -> str:
    """Получает название команды удаления для пользователя."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT delete_cmd FROM settings WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result['delete_cmd'] if result else 'дд'
    except Exception as e:
        logger.error(f"Ошибка при получении delete_cmd для user_id={user_id}: {e}")
        return 'дд'
    finally:
        if conn:
            conn.close()

async def set_delete_cmd(user_id: int, delete_cmd: str) -> bool:
    """Устанавливает название команды удаления для пользователя."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO settings (user_id, delete_cmd)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET delete_cmd = %s
            """, (user_id, delete_cmd, delete_cmd))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при установке delete_cmd для user_id={user_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_interval(user_id: int, interval_name: str, chat_id: int, interval_minutes: int, interval_text: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO intervals (user_id, interval_name, chat_id, interval_minutes, interval_text) VALUES (%s, %s, %s, %s, %s)",
                (user_id, interval_name, chat_id, interval_minutes, interval_text)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB Error in save_interval: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def delete_interval(user_id: int, interval_name: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM intervals WHERE user_id = %s AND interval_name = %s",
                (user_id, interval_name)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error in delete_interval: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_intervals(user_id: int) -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT interval_name, chat_id, interval_minutes, interval_text FROM intervals WHERE user_id = %s",
                (user_id,)
            )
            return [{
                'interval_name': row[0],
                'chat_id': row[1],
                'interval_minutes': row[2],
                'interval_text': row[3]
            } for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"DB Error in list_intervals: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def count_intervals(user_id: int) -> int:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM intervals WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"DB Error in count_intervals: {e}")
        return 0
    finally:
        if conn:
            conn.close()