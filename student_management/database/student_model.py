"""
Student Model
-------------
Handles all database operations for student records.
"""

import sqlite3
from database.db_manager import DatabaseManager


class StudentModel:
    """Model for student CRUD operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # The students table is created by DatabaseManager.initialize_schema()

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def insert(self, data: dict) -> bool:
        """
        Insert a new student record.

        Args:
            data: Dictionary with keys: Roll_No, Name, Email, Gender,
                  Contact, DOB, Address.

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                INSERT INTO students (Roll_No, Name, Email, Gender, Contact, DOB, Address)
                VALUES (:Roll_No, :Name, :Email, :Gender, :Contact, :DOB, :Address)
            """, data)
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"[StudentModel] Duplicate roll number: {data.get('Roll_No')}")
            return False
        except sqlite3.Error as e:
            print(f"[StudentModel] Insert error: {e}")
            return False
        finally:
            conn.close()

    def update(self, data: dict) -> bool:
        """
        Update an existing student record.

        Args:
            data: Dictionary containing Roll_No and fields to update.

        Returns:
            True if at least one row was affected, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                UPDATE students
                SET Name=:Name, Email=:Email, Gender=:Gender,
                    Contact=:Contact, DOB=:DOB, Address=:Address
                WHERE Roll_No=:Roll_No
            """, data)
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[StudentModel] Update error: {e}")
            return False
        finally:
            conn.close()

    def delete(self, roll_no: str) -> bool:
        """
        Delete a student by roll number.

        Args:
            roll_no: The student's roll number.

        Returns:
            True if deleted, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("DELETE FROM students WHERE Roll_No=?", (roll_no,))
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[StudentModel] Delete error: {e}")
            return False
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  QUERY METHODS
    # ─────────────────────────────────────────────────────────────
    def fetch_all(self) -> list:
        """
        Retrieve all student records ordered by Roll_No.

        Returns:
            List of dictionaries representing student rows.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT * FROM students ORDER BY Roll_No")
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[StudentModel] Fetch all error: {e}")
            return []
        finally:
            conn.close()

    def get_by_roll(self, roll_no: str) -> dict | None:
        """
        Fetch a single student by roll number.

        Args:
            roll_no: Student roll number.

        Returns:
            Dictionary with student data, or None if not found.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT * FROM students WHERE Roll_No=?", (roll_no,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[StudentModel] Get by roll error: {e}")
            return None
        finally:
            conn.close()

    def search(self, field: str, value: str) -> list:
        """
        Search students by Roll_No or Name using partial match.

        Args:
            field: 'Roll_No' or 'Name'.
            value: Search term.

        Returns:
            List of matching student records.
        """
        allowed_fields = {"Roll_No", "Name"}
        if field not in allowed_fields:
            print(f"[StudentModel] Invalid search field: {field}")
            return []

        try:
            conn, cur = self.db_manager._connect()
            query = f"SELECT * FROM students WHERE {field} LIKE ? ORDER BY Roll_No"
            cur.execute(query, (f"%{value}%",))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[StudentModel] Search error: {e}")
            return []
        finally:
            conn.close()

    def roll_exists(self, roll_no: str) -> bool:
        """
        Check if a roll number already exists.

        Args:
            roll_no: Student roll number.

        Returns:
            True if the roll number is in use.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT 1 FROM students WHERE Roll_No=?", (roll_no,))
            return cur.fetchone() is not None
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def count(self) -> int:
        """Return total number of students."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT COUNT(*) FROM students")
            return cur.fetchone()[0]
        except sqlite3.Error:
            return 0
        finally:
            conn.close()