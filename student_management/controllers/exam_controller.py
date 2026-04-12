"""
Exam Controller
---------------
Manages business logic for exam-related operations.
Acts as an intermediary between views and the ExamModel.
"""

from datetime import datetime
from database.exam_model import ExamModel
from utils.validators import validate_date


class ExamController:
    """Controller for exam records and performance calculations."""

    def __init__(self, db_manager):
        """
        Initialize the controller with a database manager.

        Args:
            db_manager: DatabaseManager instance.
        """
        self.db_manager = db_manager
        self.exam_model = ExamModel(db_manager)

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def add_exam(self, data: dict) -> tuple[bool, str]:
        """
        Add a new exam record after validation.

        Args:
            data: Dictionary with keys:
                - roll_no (required)
                - subject (required)
                - exam_date (optional, default today)
                - marks_obtained (required, float)
                - max_marks (required, float)
                - exam_type (optional)

        Returns:
            Tuple (success, message).
        """
        # Validate required fields
        required = ['roll_no', 'subject', 'marks_obtained', 'max_marks']
        for field in required:
            if field not in data or not str(data[field]).strip():
                return False, f"{field.replace('_', ' ').title()} is required."

        # Validate marks
        try:
            marks = float(data['marks_obtained'])
            max_marks = float(data['max_marks'])
            if marks < 0 or max_marks <= 0:
                return False, "Marks must be non-negative and max marks must be positive."
            if marks > max_marks:
                return False, "Marks obtained cannot exceed maximum marks."
        except (ValueError, TypeError):
            return False, "Marks must be valid numbers."

        # Validate date if provided
        exam_date = data.get('exam_date', '').strip()
        if exam_date and not validate_date(exam_date, "%Y-%m-%d"):
            return False, "Exam date must be in YYYY-MM-DD format."

        # Set default date if empty
        if not exam_date:
            exam_date = datetime.now().strftime("%Y-%m-%d")

        # Prepare data for insertion
        record = {
            'roll_no': data['roll_no'].strip(),
            'subject': data['subject'].strip(),
            'exam_date': exam_date,
            'marks_obtained': marks,
            'max_marks': max_marks,
            'exam_type': data.get('exam_type', '').strip() or None
        }

        # Insert into database
        if self.exam_model.insert(record):
            return True, "Exam record added successfully."
        else:
            return False, "Failed to add exam record."

    def update_exam(self, exam_id: int, data: dict) -> tuple[bool, str]:
        """
        Update an existing exam record.

        Args:
            exam_id: The exam record ID.
            data: Dictionary with fields to update.

        Returns:
            Tuple (success, message).
        """
        # Get existing record to validate marks
        existing = self.exam_model.get_by_id(exam_id)
        if not existing:
            return False, "Exam record not found."

        update_data = {}
        if 'subject' in data:
            update_data['subject'] = data['subject'].strip()
        if 'exam_date' in data:
            date_str = data['exam_date'].strip()
            if date_str and not validate_date(date_str, "%Y-%m-%d"):
                return False, "Exam date must be in YYYY-MM-DD format."
            update_data['exam_date'] = date_str if date_str else None
        if 'exam_type' in data:
            update_data['exam_type'] = data['exam_type'].strip() or None

        # Handle marks
        marks = data.get('marks_obtained')
        max_marks = data.get('max_marks')
        if marks is not None and max_marks is not None:
            try:
                marks_val = float(marks)
                max_val = float(max_marks)
                if marks_val < 0 or max_val <= 0:
                    return False, "Marks must be non-negative and max marks positive."
                if marks_val > max_val:
                    return False, "Marks obtained cannot exceed maximum marks."
                update_data['marks_obtained'] = marks_val
                update_data['max_marks'] = max_val
            except (ValueError, TypeError):
                return False, "Marks must be valid numbers."
        elif marks is not None:
            # Partial update: keep existing max_marks, check against it
            try:
                marks_val = float(marks)
                if marks_val < 0:
                    return False, "Marks obtained must be non-negative."
                if marks_val > existing['max_marks']:
                    return False, "Marks obtained cannot exceed maximum marks."
                update_data['marks_obtained'] = marks_val
            except (ValueError, TypeError):
                return False, "Marks must be a valid number."
        elif max_marks is not None:
            try:
                max_val = float(max_marks)
                if max_val <= 0:
                    return False, "Maximum marks must be positive."
                if existing['marks_obtained'] > max_val:
                    return False, "Existing marks obtained exceed new maximum marks."
                update_data['max_marks'] = max_val
            except (ValueError, TypeError):
                return False, "Maximum marks must be a valid number."

        if not update_data:
            return False, "No fields to update."

        if self.exam_model.update(exam_id, update_data):
            return True, "Exam record updated successfully."
        else:
            return False, "Failed to update exam record."

    def delete_exam(self, exam_id: int) -> tuple[bool, str]:
        """
        Delete an exam record.

        Args:
            exam_id: The exam record ID.

        Returns:
            Tuple (success, message).
        """
        if self.exam_model.delete(exam_id):
            return True, "Exam record deleted successfully."
        else:
            return False, "Exam record not found or could not be deleted."

    # ─────────────────────────────────────────────────────────────
    #  QUERY METHODS
    # ─────────────────────────────────────────────────────────────
    def get_student_exams(self, roll_no: str) -> list:
        """
        Get all exam records for a student, sorted by date descending.

        Args:
            roll_no: Student roll number.

        Returns:
            List of exam dictionaries.
        """
        if not roll_no or not roll_no.strip():
            return []
        return self.exam_model.get_by_roll(roll_no.strip())

    def get_recent_exams(self, roll_no: str, limit: int = 5) -> list:
        """
        Get recent exam records for a student.

        Args:
            roll_no: Student roll number.
            limit: Maximum number of records.

        Returns:
            List of exam dictionaries.
        """
        if not roll_no or not roll_no.strip():
            return []
        return self.exam_model.get_recent_by_roll(roll_no.strip(), limit)

    def get_subject_exams(self, roll_no: str, subject: str) -> list:
        """
        Get all exam records for a student in a specific subject.

        Args:
            roll_no: Student roll number.
            subject: Subject name.

        Returns:
            List of exam dictionaries.
        """
        if not roll_no or not roll_no.strip() or not subject:
            return []
        return self.exam_model.get_by_subject(roll_no.strip(), subject.strip())

    # ─────────────────────────────────────────────────────────────
    #  PERFORMANCE CALCULATIONS
    # ─────────────────────────────────────────────────────────────
    def get_subject_averages(self, roll_no: str) -> dict:
        """
        Get average percentage for each subject for a student.

        Args:
            roll_no: Student roll number.

        Returns:
            Dictionary mapping subject to average percentage.
        """
        if not roll_no or not roll_no.strip():
            return {}
        return self.exam_model.get_subject_averages(roll_no.strip())

    def get_overall_performance(self, roll_no: str) -> dict:
        """
        Get overall performance metrics for a student.

        Returns:
            Dict with: total_exams, average_percentage, best_subject, worst_subject.
        """
        if not roll_no or not roll_no.strip():
            return {"total_exams": 0, "average_percentage": 0, "best_subject": None, "worst_subject": None}
        return self.exam_model.get_overall_performance(roll_no.strip())

    def get_performance_trend(self, roll_no: str, subject: str) -> list:
        """
        Get performance trend for a subject over time.

        Args:
            roll_no: Student roll number.
            subject: Subject name.

        Returns:
            List of dicts with date and percentage.
        """
        exams = self.get_subject_exams(roll_no, subject)
        trend = []
        for exam in exams:
            percentage = (exam['marks_obtained'] / exam['max_marks'] * 100) if exam['max_marks'] else 0
            trend.append({
                'date': exam.get('exam_date', 'N/A'),
                'percentage': round(percentage, 2)
            })
        # Sort by date ascending
        trend.sort(key=lambda x: x['date'] if x['date'] != 'N/A' else '')
        return trend

    # ─────────────────────────────────────────────────────────────
    #  BULK OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def bulk_import_exams(self, records: list) -> tuple[int, list]:
        """
        Import multiple exam records, validating each.

        Args:
            records: List of dictionaries with exam data.

        Returns:
            Tuple (success_count, errors_list).
        """
        success_count = 0
        errors = []

        for idx, rec in enumerate(records):
            success, msg = self.add_exam(rec)
            if success:
                success_count += 1
            else:
                errors.append(f"Row {idx+1}: {msg}")

        return success_count, errors

    def get_all_subjects(self) -> list:
        """
        Get a list of all distinct subjects across all exams.

        Returns:
            Sorted list of subject names.
        """
        return self.exam_model.get_subject_list()