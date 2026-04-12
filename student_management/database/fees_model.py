"""
Fees Model
----------
Handles database operations for student fee structures and payments.
"""

import sqlite3
from datetime import datetime
from database.db_manager import DatabaseManager


class FeesModel:
    """Model for fee records and payment management."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._ensure_table()

    def _ensure_table(self):
        """Create the fees table if it does not exist."""
        try:
            conn, cur = self.db_manager._connect()
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
            conn.commit()
        except sqlite3.Error as e:
            print(f"[FeesModel] Table creation error: {e}")
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def insert_fee_structure(self, data: dict) -> bool:
        """
        Insert a new fee structure for a student.

        Args:
            data: Dictionary with keys: roll_no, academic_year, term,
                  total_amount, paid_amount (default 0), due_date (optional).

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                INSERT INTO fees (roll_no, academic_year, term, total_amount, paid_amount, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['roll_no'],
                data['academic_year'],
                data['term'],
                data['total_amount'],
                data.get('paid_amount', 0.0),
                data.get('due_date')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"[FeesModel] Duplicate fee structure for {data['roll_no']} - {data['term']}")
            return False
        except sqlite3.Error as e:
            print(f"[FeesModel] Insert error: {e}")
            return False
        finally:
            conn.close()

    def update_fee_structure(self, fee_id: int, data: dict) -> bool:
        """
        Update an existing fee structure.

        Args:
            fee_id: The fee record ID.
            data: Dictionary with fields to update.

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            fields = []
            values = []
            for key in ['academic_year', 'term', 'total_amount', 'due_date']:
                if key in data:
                    fields.append(f"{key} = ?")
                    values.append(data[key])
            if not fields:
                return False
            values.append(fee_id)
            query = f"UPDATE fees SET {', '.join(fields)} WHERE id = ?"
            cur.execute(query, values)
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[FeesModel] Update error: {e}")
            return False
        finally:
            conn.close()

    def delete_fee_structure(self, fee_id: int) -> bool:
        """Delete a fee structure by ID."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("DELETE FROM fees WHERE id = ?", (fee_id,))
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[FeesModel] Delete error: {e}")
            return False
        finally:
            conn.close()

    def get_by_id(self, fee_id: int) -> dict | None:
        """Retrieve a single fee record by ID."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT * FROM fees WHERE id = ?", (fee_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[FeesModel] Fetch by ID error: {e}")
            return None
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  PAYMENT OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def record_payment(self, fee_id: int, new_paid_amount: float, payment_date: str = None) -> bool:
        """
        Update the paid amount for a fee record.

        Args:
            fee_id: The fee record ID.
            new_paid_amount: The new total paid amount (should be ≥ previous).
            payment_date: Date of payment (defaults to today).

        Returns:
            True if successful, False otherwise.
        """
        if payment_date is None:
            payment_date = datetime.now().strftime("%Y-%m-%d")
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                UPDATE fees
                SET paid_amount = ?, last_payment_date = ?
                WHERE id = ?
            """, (new_paid_amount, payment_date, fee_id))
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[FeesModel] Payment recording error: {e}")
            return False
        finally:
            conn.close()

    def add_payment(self, fee_id: int, amount: float) -> bool:
        """
        Add an amount to the current paid amount (increment).

        Args:
            fee_id: The fee record ID.
            amount: Additional amount paid.

        Returns:
            True if successful, False otherwise.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT paid_amount, total_amount FROM fees WHERE id = ?", (fee_id,))
            row = cur.fetchone()
            if not row:
                return False
            current_paid = row['paid_amount']
            new_paid = current_paid + amount
            # Optionally cap at total_amount? Not required, may allow overpayment.
            return self.record_payment(fee_id, new_paid)
        except sqlite3.Error as e:
            print(f"[FeesModel] Add payment error: {e}")
            return False
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  QUERY METHODS
    # ─────────────────────────────────────────────────────────────
    def get_by_roll(self, roll_no: str) -> list:
        """
        Retrieve all fee records for a student.

        Args:
            roll_no: Student roll number.

        Returns:
            List of fee record dictionaries.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT * FROM fees
                WHERE roll_no = ?
                ORDER BY academic_year DESC, term
            """, (roll_no,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[FeesModel] Fetch by roll error: {e}")
            return []
        finally:
            conn.close()

    def fetch_all(self) -> list:
        """Retrieve all fee records."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT * FROM fees ORDER BY roll_no, academic_year, term")
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[FeesModel] Fetch all error: {e}")
            return []
        finally:
            conn.close()

    def fetch_all_with_student_names(self) -> list:
        """
        Retrieve all fee records joined with student names.

        Returns:
            List of dictionaries containing fee fields plus 'student_name'.
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT f.*, s.Name as student_name
                FROM fees f
                JOIN students s ON f.roll_no = s.Roll_No
                ORDER BY f.roll_no, f.academic_year, f.term
            """)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[FeesModel] Fetch with names error: {e}")
            return []
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────
    #  SUMMARY & STATISTICS
    # ─────────────────────────────────────────────────────────────
    def get_summary_by_roll(self, roll_no: str) -> dict:
        """
        Get aggregated fee summary for a student across all terms.

        Returns:
            Dict with: total_fee, paid, due, status ('PAID', 'PARTIAL', 'UNPAID', 'OVERDUE').
        """
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT
                    SUM(total_amount) as total_fee,
                    SUM(paid_amount) as paid,
                    SUM(total_amount - paid_amount) as due,
                    MIN(due_date) as earliest_due
                FROM fees
                WHERE roll_no = ?
            """, (roll_no,))
            row = cur.fetchone()
            if not row or row['total_fee'] is None:
                return {"total_fee": 0.0, "paid": 0.0, "due": 0.0, "status": "NO_RECORDS"}

            total_fee = row['total_fee'] or 0.0
            paid = row['paid'] or 0.0
            due = row['due'] or 0.0
            earliest_due = row['earliest_due']

            # Determine status
            if due <= 0:
                status = "PAID"
            else:
                # Check for overdue
                if earliest_due:
                    try:
                        due_date = datetime.strptime(earliest_due, "%Y-%m-%d").date()
                        if due_date < datetime.now().date():
                            status = "OVERDUE"
                        else:
                            status = "UNPAID" if paid == 0 else "PARTIAL"
                    except ValueError:
                        status = "UNPAID" if paid == 0 else "PARTIAL"
                else:
                    status = "UNPAID" if paid == 0 else "PARTIAL"

            return {
                "total_fee": total_fee,
                "paid": paid,
                "due": due,
                "status": status
            }
        except sqlite3.Error as e:
            print(f"[FeesModel] Summary error: {e}")
            return {"total_fee": 0.0, "paid": 0.0, "due": 0.0, "status": "ERROR"}
        finally:
            conn.close()

    def get_outstanding_total(self) -> float:
        """Return the total outstanding due across all students."""
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("SELECT SUM(total_amount - paid_amount) FROM fees")
            row = cur.fetchone()
            return row[0] if row and row[0] else 0.0
        except sqlite3.Error as e:
            print(f"[FeesModel] Outstanding total error: {e}")
            return 0.0
        finally:
            conn.close()

    def get_overdue_students(self) -> list:
        """
        Get list of students with overdue fees.

        Returns:
            List of dicts with roll_no, student_name, total_due.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            conn, cur = self.db_manager._connect()
            cur.execute("""
                SELECT f.roll_no, s.Name as student_name, SUM(f.total_amount - f.paid_amount) as total_due
                FROM fees f
                JOIN students s ON f.roll_no = s.Roll_No
                WHERE f.due_date < ? AND (f.total_amount - f.paid_amount) > 0
                GROUP BY f.roll_no, s.Name
                ORDER BY total_due DESC
            """, (today,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[FeesModel] Overdue students error: {e}")
            return []
        finally:
            conn.close()