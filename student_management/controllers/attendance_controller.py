"""
Attendance Controller
---------------------
Manages business logic for attendance operations.
Validates input and coordinates with AttendanceModel.
"""

from datetime import datetime
from database.attendance_model import AttendanceModel
from utils.validators import validate_date


class AttendanceController:
    """Controller for attendance-related operations."""

    def __init__(self, db_manager):
        """
        Initialize the controller with a database manager.

        Args:
            db_manager: DatabaseManager instance.
        """
        self.db_manager = db_manager
        self.attendance_model = AttendanceModel(db_manager)

    # ─────────────────────────────────────────────────────────────
    #  VALIDATION
    # ─────────────────────────────────────────────────────────────
    def validate_attendance_record(self, roll_no: str, date: str, status: str) -> tuple[bool, str]:
        """
        Validate a single attendance record.

        Args:
            roll_no: Student roll number.
            date: Date in YYYY-MM-DD format.
            status: 'Present', 'Absent', or 'Late'.

        Returns:
            Tuple (is_valid, error_message).
        """
        if not roll_no or not roll_no.strip():
            return False, "Roll number is required."

        if not date or not date.strip():
            return False, "Date is required."

        if not validate_date(date, "%Y-%m-%d"):
            return False, "Date must be in YYYY-MM-DD format and be a valid date."

        if status not in ('Present', 'Absent', 'Late'):
            return False, "Status must be 'Present', 'Absent', or 'Late'."

        return True, ""

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def mark_attendance(self, roll_no: str, date: str, status: str) -> tuple[bool, str]:
        """
        Mark or update attendance for a student on a specific date.

        Returns:
            Tuple (success, message).
        """
        valid, msg = self.validate_attendance_record(roll_no, date, status)
        if not valid:
            return False, msg

        if self.attendance_model.insert_or_update(roll_no, date, status):
            return True, f"Attendance marked as {status}."
        else:
            return False, "Database error: Could not mark attendance."

    def get_attendance_by_date(self, date: str) -> list:
        """
        Get all attendance records for a specific date.

        Args:
            date: Date in YYYY-MM-DD format.

        Returns:
            List of attendance records.
        """
        if not date or not validate_date(date, "%Y-%m-%d"):
            return []
        return self.attendance_model.get_by_date(date)

    # ─────────────────────────────────────────────────────────────
    #  BULK OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def bulk_mark_attendance(self, records: list) -> tuple[int, list]:
        """
        Mark attendance for multiple students at once.

        Args:
            records: List of dicts with keys 'roll_no', 'date', 'status'.

        Returns:
            Tuple (success_count, errors_list).
        """
        valid_records = []
        errors = []

        for idx, rec in enumerate(records):
            valid, msg = self.validate_attendance_record(
                rec.get('roll_no', ''),
                rec.get('date', ''),
                rec.get('status', '')
            )
            if valid:
                valid_records.append((rec['roll_no'], rec['date'], rec['status']))
            else:
                errors.append(f"Row {idx+1}: {msg}")

        if valid_records:
            if self.attendance_model.bulk_upsert(valid_records):
                return len(valid_records), errors
            else:
                return 0, ["Database error during bulk insert."] + errors

        return 0, errors

    # ─────────────────────────────────────────────────────────────
    #  SUMMARY & STATISTICS
    # ─────────────────────────────────────────────────────────────
    def get_student_attendance_summary(self, roll_no: str) -> dict:
        """
        Get attendance summary for a student.

        Returns:
            Dict with total_days, present, absent, late, percentage.
        """
        if not roll_no:
            return {"total_days": 0, "present": 0, "absent": 0, "late": 0, "percentage": 0.0}
        return self.attendance_model.get_summary_by_roll(roll_no)

    def get_all_students_attendance_for_date(self, date: str) -> list:
        """
        Get attendance status for all students on a given date.
        Includes students with no record (default 'Absent').

        Returns:
            List of dicts with Roll_No, Name, status.
        """
        if not date or not validate_date(date, "%Y-%m-%d"):
            return []
        return self.attendance_model.get_all_students_attendance_for_date(date)

    def get_monthly_summary(self, year: int, month: int) -> list:
        """
        Get monthly attendance summary for all students.

        Returns:
            List of dicts with Roll_No, Name, Present, Absent, Late.
        """
        if not (1 <= month <= 12) or year < 2000:
            return []
        return self.attendance_model.get_monthly_summary(year, month)