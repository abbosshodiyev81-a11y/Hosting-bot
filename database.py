import sqlite3
import json

class Database:
    def __init__(self, db_name="hosting.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                name TEXT,
                token TEXT,
                status TEXT DEFAULT 'stopped',
                path TEXT,
                env_vars TEXT DEFAULT '{}',
                FOREIGN KEY (owner_id) REFERENCES users (telegram_id)
            )
        """)
        self.conn.commit()

    def add_user(self, telegram_id, username):
        try:
            self.cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
            self.conn.commit()
        except Exception as e:
            print(f"add_user xatosi: {e}")

    def add_bot(self, owner_id, name, token, path):
        try:
            self.cursor.execute("INSERT INTO bots (owner_id, name, token, path) VALUES (?, ?, ?, ?)", 
                              (owner_id, name, token, path))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"add_bot xatosi: {e}")
            return None

    def get_user_bots(self, owner_id):
        try:
            self.cursor.execute("SELECT * FROM bots WHERE owner_id = ?", (owner_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"get_user_bots xatosi: {e}")
            return []

    def get_bot(self, bot_id):
        try:
            self.cursor.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"get_bot xatosi: {e}")
            return None

    def update_bot_status(self, bot_id, status):
        try:
            self.cursor.execute("UPDATE bots SET status = ? WHERE id = ?", (status, bot_id))
            self.conn.commit()
        except Exception as e:
            print(f"update_bot_status xatosi: {e}")

    def delete_bot(self, bot_id):
        try:
            self.cursor.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
            self.conn.commit()
        except Exception as e:
            print(f"delete_bot xatosi: {e}")

    def update_env_vars(self, bot_id, env_vars):
        try:
            self.cursor.execute("UPDATE bots SET env_vars = ? WHERE id = ?", 
                              (json.dumps(env_vars), bot_id))
            self.conn.commit()
        except Exception as e:
            print(f"update_env_vars xatosi: {e}")

    def get_all_users(self):
        try:
            self.cursor.execute("SELECT * FROM users")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"get_all_users xatosi: {e}")
            return []

    def get_all_bots(self):
        try:
            self.cursor.execute("SELECT * FROM bots")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"get_all_bots xatosi: {e}")
            return []