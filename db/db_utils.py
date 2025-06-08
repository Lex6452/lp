import psycopg2
from typing import Optional, List, Dict
from config import db_config
import os

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
            """)
            conn.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")
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
        print(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_template(user_id: int, template_name: str, template_text: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO templates (user_id, template_name, template_text) VALUES (%s, %s, %s)",
                (user_id, template_name, template_text)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def get_template(user_id: int, template_name: str) -> Optional[str]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT template_text FROM templates WHERE user_id = %s AND template_name = %s",
                (user_id, template_name)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_templates(user_id: int) -> List[str]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT template_name FROM templates WHERE user_id = %s ORDER BY template_name",
                (user_id,)
            )
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def save_voice_message(user_id: int, voice_name: str, file_path: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO voice_messages (user_id, voice_name, file_path) VALUES (%s, %s, %s)",
                (user_id, voice_name, file_path)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

async def list_voice_messages(user_id: int) -> List[Dict[str, str]]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT voice_name, file_path FROM voice_messages WHERE user_id = %s ORDER BY voice_name",
                (user_id,)
            )
            return [{"name": row[0], "file_path": row[1]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

async def get_voice_message(user_id: int, voice_name: str) -> Optional[str]:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_path FROM voice_messages WHERE user_id = %s AND voice_name = %s",
                (user_id, voice_name)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"DB Error: {e}")
        return None
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
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
        print(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()
