"""
Exam Model
----------
Handles all database operations related to student exam scores.
"""

import sqlite3
from database.db_manager import DatabaseManager


class ExamModel:
    """Model for exam records and score management."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_table()

    def _ensure_table(self):
        """Create the exams table if it does not exist."""
        try:
            conn, cur = self.db_manager._connect()
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
        except sqlite3.Error as e:
            print(f"[ExamModel] Table creation error: {e}")
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def insert(self, data: dict) -> bool:
        """
        Insert a new exam record.

        Args:
            data: Dictionary with keys: roll_no, subject, exam_date (optional),
                  marks_obtained, max_marks, exam_type (optional).

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                INSERT INTO exams (roll_no, subject, exam_date, marks_obtained, max_marks, exam_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get('roll_no'),
                data.get('subject'),
                data.get('exam_date'),
                data.get('marks_obtained'),
                data.get('max_marks'),
                data.get('exam_type')
            ))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ExamModel] Insert error: {e}")
            return False
        finally:
            conn.close()

    def update(self, exam_id: int, data: dict) -> bool:
        """
        Update an existing exam record by ID.

        Args:
            exam_id: The exam record ID.
            data: Dictionary with fields to update.

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            fields = []
            values = []
            for key in ['subject', 'exam_date', 'marks_obtained', 'max_marks', 'exam_type']:
                if key in data:
                    fields.append(f"{key} = ?")
                    values.append(data[key])
            if not fields:
                return False
            values.append(exam_id)
            query = f"UPDATE exams SET {', '.join(fields)} WHERE id = ?"
            cur.execute(query, values)
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ExamModel] Update error: {e}")
            return False
        finally:
            conn.close()

    def delete(self, exam_id: int) -> bool:
        """Delete an exam record by ID."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ExamModel] Delete error: {e}")
            return False
        finally:
            conn.close()

    def get_by_id(self, exam_id: int) -> dict | None:
        """Retrieve a single exam record by ID."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[ExamModel] Fetch by ID error: {e}")
            return None
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  QUERY METHODS
    # ─────────────────────────────────────────────────────────────
    def get_by_roll(self, roll_no: str) -> list:
        """
        Retrieve all exam records for a student, sorted by date descending.

        Args:
            roll_no: Student roll number.

        Returns:
            List of exam record dictionaries.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT * FROM exams
                WHERE roll_no = ?
                ORDER BY exam_date DESC, subject
            """, (roll_no,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[ExamModel] Fetch by roll error: {e}")
            return []
        finally:
            conn.close()

    def get_recent_by_roll(self, roll_no: str, limit: int = 5) -> list:
        """
        Retrieve the most recent exam records for a student.

        Args:
            roll_no: Student roll number.
            limit: Maximum number of records to return.

        Returns:
            List of exam records, newest first.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT * FROM exams
                WHERE roll_no = ?
                ORDER BY exam_date DESC
                LIMIT ?
            """, (roll_no, limit))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[ExamModel] Recent fetch error: {e}")
            return []
        finally:
            conn.close()

    def get_by_subject(self, roll_no: str, subject: str) -> list:
        """
        Retrieve all exam records for a student in a specific subject.

        Args:
            roll_no: Student roll number.
            subject: Subject name.

        Returns:
            List of exam records.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT * FROM exams
                WHERE roll_no = ? AND subject = ?
                ORDER BY exam_date DESC
            """, (roll_no, subject))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[ExamModel] Subject fetch error: {e}")
            return []
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  STATISTICS AND SUMMARIES
    # ─────────────────────────────────────────────────────────────
    def get_subject_averages(self, roll_no: str) -> dict:
        """
        Calculate average percentage for each subject for a student.

        Args:
            roll_no: Student roll number.

        Returns:
            Dictionary mapping subject to average percentage.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT
                    subject,
                    AVG(marks_obtained / max_marks * 100) as avg_percentage
                FROM exams
                WHERE roll_no = ? AND max_marks > 0
                GROUP BY subject
                ORDER BY subject
            """, (roll_no,))
            rows = cur.fetchall()
            return {row['subject']: round(row['avg_percentage'], 2) for row in rows}
        except sqlite3.Error as e:
            print(f"[ExamModel] Averages error: {e}")
            return {}
        finally:
            conn.close()

    def get_overall_performance(self, roll_no: str) -> dict:
        """
        Calculate overall performance metrics for a student.

        Returns:
            Dict with: total_exams, average_percentage, best_subject, worst_subject.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT
                    COUNT(*) as total_exams,
                    AVG(marks_obtained / max_marks * 100) as overall_avg
                FROM exams
                WHERE roll_no = ? AND max_marks > 0
            """, (roll_no,))
            row = cur.fetchone()
            if not row or row['total_exams'] == 0:
                return {"total_exams": 0, "average_percentage": 0, "best_subject": None, "worst_subject": None}

            # Get best and worst subjects by average
            cur.execute("""
                SELECT
                    subject,
                    AVG(marks_obtained / max_marks * 100) as avg_pct
                FROM exams
                WHERE roll_no = ? AND max_marks > 0
                GROUP BY subject
                ORDER BY avg_pct DESC
            """, (roll_no,))
            subjects = cur.fetchall()
            best = subjects[0]['subject'] if subjects else None
            worst = subjects[-1]['subject'] if subjects else None

            return {
                "total_exams": row['total_exams'],
                "average_percentage": round(row['overall_avg'], 2) if row['overall_avg'] else 0,
                "best_subject": best,
                "worst_subject": worst
            }
        except sqlite3.Error as e:
            print(f"[ExamModel] Overall performance error: {e}")
            return {"total_exams": 0, "average_percentage": 0, "best_subject": None, "worst_subject": None}
        finally:
            conn.close()

    def get_subject_list(self) -> list:
        """Return a list of all distinct subjects across all exams."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT DISTINCT subject FROM exams ORDER BY subject")
            return [row['subject'] for row in cur.fetchall()]
        except sqlite3.Error as e:
            print(f"[ExamModel] Subject list error: {e}")
            return []
        finally:
            conn.close()

    def bulk_insert(self, records: list) -> bool:
        """
        Insert multiple exam records at once.

        Args:
            records: List of dictionaries with exam fields.

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            for rec in records:
                cur.execute("""
                    INSERT INTO exams (roll_no, subject, exam_date, marks_obtained, max_marks, exam_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rec.get('roll_no'),
                    rec.get('subject'),
                    rec.get('exam_date'),
                    rec.get('marks_obtained'),
                    rec.get('max_marks'),
                    rec.get('exam_type')
                ))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ExamModel] Bulk insert error: {e}")
            return False
        finally:
            conn.close()