"""
Database Manager
----------------
Core SQLite3 connection handling and schema management.
All models use this class to interact with the database.
"""

import sqlite3
import os
from config import DATABASE_NAME


class DatabaseManager:
    """Manages SQLite database connections and table creation."""

    def __init__(self, db_name: str = DATABASE_NAME):
        """
        Initialize the database manager.

        Args:
            db_name: Name of the SQLite database file.
        """
        self.db_name = db_name
        self.db_path = self._get_db_path()

    def _get_db_path(self) -> str:
        """Return the absolute path to the database file."""
        # Assuming db_manager.py is inside 'database/' folder,
        # the database file is at the project root (one level up).
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, self.db_name)

    def _connect(self):
        """
        Create and return a new database connection and cursor.

        Returns:
            tuple: (connection, cursor) with row_factory set to sqlite3.Row.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # allows dict-like access
        cur = conn.cursor()
        # Enable foreign key constraints
        cur.execute("PRAGMA foreign_keys = ON;")
        return conn, cur

    def initialize_schema(self):
        """
        Create all necessary tables if they do not already exist.
        This method is idempotent and safe to call multiple times.
        """
        conn, cur = self._connect()
        try:
            # Students table (core)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    Roll_No  TEXT PRIMARY KEY,
                    Name     TEXT NOT NULL,
                    Email    TEXT NOT NULL,
                    Gender   TEXT NOT NULL,
                    Contact  TEXT NOT NULL,
                    DOB      TEXT NOT NULL,
                    Address  TEXT NOT NULL
                )
            """)

            # Attendance table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT CHECK(status IN ('Present', 'Absent', 'Late')) NOT NULL,
                    FOREIGN KEY (roll_no) REFERENCES students(Roll_No) ON DELETE CASCADE,
                    UNIQUE(roll_no, date)
                )
            """)

            # Fees table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL,
                    academic_year TEXT NOT NULL,
                    term TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    paid_amount REAL DEFAULT 0,
                    due_date TEXT,
                    last_payment_date TEXT,
                    FOREIGN KEY (roll_no) REFERENCES students(Roll_No) ON DELETE CASCADE,
                    UNIQUE(roll_no, academic_year, term)
                )
            """)

            # Exams table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    exam_date TEXT,
                    marks_obtained REAL,
                    max_marks REAL,
                    exam_type TEXT,
                    FOREIGN KEY (roll_no) REFERENCES students(Roll_No) ON DELETE CASCADE
                )
            """)

            conn.commit()
            print("[DatabaseManager] Schema initialized successfully.")
        except sqlite3.Error as e:
            print(f"[DatabaseManager] Schema initialization error: {e}")
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Execute a SELECT query and return results as list of dicts.

        Args:
            query: SQL query string.
            params: Tuple of parameters for the query.

        Returns:
            List of dictionaries representing rows.
        """
        conn, cur = self._connect()
        try:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[DatabaseManager] Query error: {e}")
            return []
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string.
            params: Tuple of parameters.

        Returns:
            True if at least one row was affected, False otherwise.
        """
        conn, cur = self._connect()
        try:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[DatabaseManager] Update error: {e}")
            return False
        finally:
            conn.close()

    def execute_many(self, query: str, params_list: list) -> bool:
        """
        Execute a batch INSERT or REPLACE query.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.

        Returns:
            True if successful, False on error.
        """
        conn, cur = self._connect()
        try:
            cur.executemany(query, params_list)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DatabaseManager] Batch execution error: {e}")
            return False
        finally:
            conn.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        conn, cur = self._connect()
        try:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cur.fetchone() is not None
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def backup_database(self, backup_path: str = None) -> bool:
        """
        Create a backup copy of the database.

        Args:
            backup_path: Destination path. If None, generates a timestamped name.

        Returns:
            True if backup successful, False otherwise.
        """
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"students_backup_{timestamp}.db"

        try:
            source = sqlite3.connect(self.db_path)
            dest = sqlite3.connect(backup_path)
            source.backup(dest)
            source.close()
            dest.close()
            print(f"[DatabaseManager] Backup created at {backup_path}")
            return True
        except sqlite3.Error as e:
            print(f"[DatabaseManager] Backup error: {e}")
            return False