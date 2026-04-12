"""
Attendance Model
----------------
Handles all database operations related to student attendance.
"""

import sqlite3
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager


class AttendanceModel:
    """Model for attendance records."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_table()

    def _ensure_table(self):
        """Create the attendance table if it does not exist."""
        try:
            conn, cur = self.db_manager._connect()
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
            conn.commit()
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Table creation error: {e}")
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  BASIC CRUD
    # ─────────────────────────────────────────────────────────────
    def insert_or_update(self, roll_no: str, date: str, status: str) -> bool:
        """
        Insert or replace an attendance record for a student on a specific date.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                INSERT OR REPLACE INTO attendance (roll_no, date, status)
                VALUES (?, ?, ?)
            """, (roll_no, date, status))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Insert error: {e}")
            return False
        finally:
            conn.close()

    def get_by_date(self, date: str) -> list:
        """
        Fetch all attendance records for a specific date.
        Returns a list of dicts with keys: roll_no, date, status.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT roll_no, date, status FROM attendance
                WHERE date = ?
                ORDER BY roll_no
            """, (date,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Fetch error: {e}")
            return []
        finally:
            conn.close()

    def get_by_roll_and_date_range(self, roll_no: str, start_date: str, end_date: str) -> list:
        """
        Fetch attendance records for a student within a date range.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT date, status FROM attendance
                WHERE roll_no = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """, (roll_no, start_date, end_date))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Range fetch error: {e}")
            return []
        finally:
            conn.close()

    def delete_by_date(self, date: str) -> bool:
        """Delete all attendance records for a specific date."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("DELETE FROM attendance WHERE date = ?", (date,))
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Delete error: {e}")
            return False
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  BULK OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def bulk_upsert(self, records: list) -> bool:
        """
        Insert or update multiple attendance records.
        records: list of tuples (roll_no, date, status)
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.executemany("""
                INSERT OR REPLACE INTO attendance (roll_no, date, status)
                VALUES (?, ?, ?)
            """, records)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Bulk insert error: {e}")
            return False
        finally:
            conn.close()

    def bulk_upsert_from_dicts(self, dicts: list) -> bool:
        """
        Convert list of dicts to tuples and call bulk_upsert.
        Expected dict keys: 'Roll_No', 'Date', 'Status'.
        """
        records = [(d['Roll_No'], d['Date'], d['Status']) for d in dicts]
        return self.bulk_upsert(records)

    # ─────────────────────────────────────────────────────────────
    #  SUMMARY & STATISTICS
    # ─────────────────────────────────────────────────────────────
    def get_summary_by_roll(self, roll_no: str) -> dict:
        """
        Get attendance summary for a single student across all dates.
        Returns dict with: total_days, present, absent, late, percentage.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT
                    COUNT(*) as total_days,
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                    SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                    SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late
                FROM attendance
                WHERE roll_no = ?
            """, (roll_no,))
            row = cur.fetchone()
            if not row or row['total_days'] == 0:
                return {"total_days": 0, "present": 0, "absent": 0, "late": 0, "percentage": 0.0}

            total = row['total_days']
            present = row['present'] or 0
            percentage = (present / total * 100) if total > 0 else 0.0
            return {
                "total_days": total,
                "present": present,
                "absent": row['absent'] or 0,
                "late": row['late'] or 0,
                "percentage": round(percentage, 2)
            }
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Summary error: {e}")
            return {"total_days": 0, "present": 0, "absent": 0, "late": 0, "percentage": 0.0}
        finally:
            conn.close()

    def get_monthly_summary(self, year: int, month: int) -> list:
        """
        Get monthly attendance summary for all students.
        Returns list of dicts with: Roll_No, Name, Present, Absent, Late.
        """
        start_date = f"{year:04d}-{month:02d}-01"
        # Last day of month
        if month == 12:
            end_date = f"{year:04d}-12-31"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
            # Subtract one day
            end_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT
                    s.Roll_No,
                    s.Name,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present,
                    SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent,
                    SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late
                FROM students s
                LEFT JOIN attendance a ON s.Roll_No = a.roll_no
                    AND a.date BETWEEN ? AND ?
                GROUP BY s.Roll_No, s.Name
                ORDER BY s.Roll_No
            """, (start_date, end_date))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Monthly summary error: {e}")
            return []
        finally:
            conn.close()

    def get_all_students_attendance_for_date(self, date: str) -> list:
        """
        Get a list of all students with their attendance status for a given date.
        Includes students who have no record yet (default status 'Absent').
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT
                    s.Roll_No,
                    s.Name,
                    COALESCE(a.status, 'Absent') as status
                FROM students s
                LEFT JOIN attendance a ON s.Roll_No = a.roll_no AND a.date = ?
                ORDER BY s.Roll_No
            """, (date,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[AttendanceModel] Fetch with students error: {e}")
            return []
        finally:
            conn.close()