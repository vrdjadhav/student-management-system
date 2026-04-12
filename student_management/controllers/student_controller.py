"""
Student Controller
------------------
Manages business logic for student record operations.
Validates input data and coordinates with StudentModel.
"""

from database.student_model import StudentModel
from utils.validators import (
    validate_email,
    validate_phone,
    validate_date,
    validate_roll_number,
    validate_name,
    validate_address
)


class StudentController:
    """Controller for student-related operations."""

    def __init__(self, db_manager):
        """
        Initialize the controller with a database manager.

        Args:
            db_manager: DatabaseManager instance.
        """
        self.db_manager = db_manager
        self.student_model = StudentModel(db_manager)

    # ─────────────────────────────────────────────────────────────
    #  VALIDATION
    # ─────────────────────────────────────────────────────────────
    def validate_student_data(self, data: dict, check_roll_exists: bool = False) -> tuple[bool, str]:
        """
        Validate a complete student record.

        Args:
            data: Dictionary with keys: Roll_No, Name, Email, Gender, Contact, DOB, Address.
            check_roll_exists: If True, verify the roll number is not already in use.

        Returns:
            Tuple (is_valid, error_message).
        """
        # Required fields
        required = ['Roll_No', 'Name', 'Email', 'Gender', 'Contact', 'DOB', 'Address']
        for field in required:
            if field not in data or not str(data[field]).strip():
                return False, f"{field.replace('_', ' ')} is required."

        roll_no = data['Roll_No'].strip()
        name = data['Name'].strip()
        email = data['Email'].strip()
        gender = data['Gender'].strip()
        contact = data['Contact'].strip()
        dob = data['DOB'].strip()
        address = data['Address'].strip()

        # Roll number validation
        if not validate_roll_number(roll_no):
            return False, "Roll number must be 3-20 alphanumeric characters (hyphens and underscores allowed)."

        if check_roll_exists and self.student_model.roll_exists(roll_no):
            return False, f"Roll number '{roll_no}' already exists."

        # Name validation
        if not validate_name(name):
            return False, "Name must contain only letters, spaces, hyphens, and apostrophes (2-100 characters)."

        # Email validation
        if not validate_email(email):
            return False, "Invalid email address format."

        # Gender validation (should match combobox values)
        if gender not in ('Male', 'Female', 'Other'):
            return False, "Gender must be 'Male', 'Female', or 'Other'."

        # Contact validation
        if not validate_phone(contact):
            return False, "Contact number must be 10 digits (optionally with +91 or 0 prefix)."

        # Date of birth validation (DD/MM/YYYY)
        if not validate_date(dob, "%d/%m/%Y"):
            return False, "Date of birth must be in DD/MM/YYYY format and be a valid date."

        # Address validation
        if not validate_address(address):
            return False, "Address must be at least 5 characters long."

        return True, ""

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def add_student(self, data: dict) -> tuple[bool, str]:
        """
        Add a new student after validation.

        Args:
            data: Dictionary with all student fields.

        Returns:
            Tuple (success, message).
        """
        valid, msg = self.validate_student_data(data, check_roll_exists=True)
        if not valid:
            return False, msg

        # Prepare cleaned data
        record = {
            'Roll_No': data['Roll_No'].strip(),
            'Name': data['Name'].strip(),
            'Email': data['Email'].strip(),
            'Gender': data['Gender'].strip(),
            'Contact': data['Contact'].strip(),
            'DOB': data['DOB'].strip(),
            'Address': data['Address'].strip()
        }

        if self.student_model.insert(record):
            return True, "Student added successfully."
        else:
            return False, "Database error: Could not add student."

    def update_student(self, data: dict) -> tuple[bool, str]:
        """
        Update an existing student record.

        Args:
            data: Dictionary containing Roll_No and fields to update.

        Returns:
            Tuple (success, message).
        """
        roll_no = data.get('Roll_No', '').strip()
        if not roll_no:
            return False, "Roll number is required for update."

        # Check if student exists
        if not self.student_model.roll_exists(roll_no):
            return False, f"Student with roll number '{roll_no}' not found."

        # Validate all data (except duplicate check)
        valid, msg = self.validate_student_data(data, check_roll_exists=False)
        if not valid:
            return False, msg

        # Prepare cleaned data
        record = {
            'Roll_No': roll_no,
            'Name': data['Name'].strip(),
            'Email': data['Email'].strip(),
            'Gender': data['Gender'].strip(),
            'Contact': data['Contact'].strip(),
            'DOB': data['DOB'].strip(),
            'Address': data['Address'].strip()
        }

        if self.student_model.update(record):
            return True, "Student updated successfully."
        else:
            return False, "No changes made or update failed."

    def delete_student(self, roll_no: str) -> tuple[bool, str]:
        """
        Delete a student by roll number.

        Args:
            roll_no: Student roll number.

        Returns:
            Tuple (success, message).
        """
        if not roll_no or not roll_no.strip():
            return False, "Roll number is required."

        roll_no = roll_no.strip()
        if not self.student_model.roll_exists(roll_no):
            return False, f"Student with roll number '{roll_no}' not found."

        if self.student_model.delete(roll_no):
            return True, "Student deleted successfully."
        else:
            return False, "Failed to delete student."

    # ─────────────────────────────────────────────────────────────
    #  QUERY METHODS
    # ─────────────────────────────────────────────────────────────
    def get_all_students(self) -> list:
        """
        Retrieve all student records.

        Returns:
            List of student dictionaries.
        """
        return self.student_model.fetch_all()

    def get_student_by_roll(self, roll_no: str) -> dict | None:
        """
        Get a single student by roll number.

        Args:
            roll_no: Student roll number.

        Returns:
            Student dictionary or None.
        """
        if not roll_no:
            return None
        return self.student_model.get_by_roll(roll_no.strip())

    def search_students(self, field: str, value: str) -> list:
        """
        Search students by Roll_No or Name.

        Args:
            field: 'Roll_No' or 'Name'.
            value: Search term.

        Returns:
            List of matching student records.
        """
        if not value or not value.strip():
            return self.get_all_students()
        return self.student_model.search(field, value.strip())

    def roll_number_exists(self, roll_no: str) -> bool:
        """Check if a roll number is already registered."""
        return self.student_model.roll_exists(roll_no.strip()) if roll_no else False

    def get_total_students(self) -> int:
        """Return the total number of registered students."""
        return self.student_model.count()

    # ─────────────────────────────────────────────────────────────
    #  DATA FORMATTING
    # ─────────────────────────────────────────────────────────────
    def format_student_list_for_display(self, students: list) -> list:
        """
        Convert student records to a list of tuples for Treeview.

        Args:
            students: List of student dictionaries.

        Returns:
            List of tuples in the order of columns defined in config.
        """
        columns = ("Roll_No", "Name", "Email", "Gender", "Contact", "DOB", "Address")
        return [tuple(s.get(col, "") for col in columns) for s in students]