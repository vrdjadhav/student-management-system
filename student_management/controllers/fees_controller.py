"""
Fees Controller
---------------
Manages business logic for fee structures and payments.
"""

from datetime import datetime
from database.fees_model import FeesModel
from utils.validators import validate_date


class FeesController:
    """Controller for fee-related operations."""

    def __init__(self, db_manager):
        """
        Initialize the controller with a database manager.

        Args:
            db_manager: DatabaseManager instance.
        """
        self.db_manager = db_manager
        self.fees_model = FeesModel(db_manager)

    # ─────────────────────────────────────────────────────────────
    #  FEE STRUCTURE MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    def add_fee_structure(self, data: dict) -> tuple[bool, str]:
        """
        Add a new fee structure for a student.

        Args:
            data: Dictionary with keys:
                - roll_no (required)
                - academic_year (required)
                - term (required)
                - total_amount (required, positive float)
                - paid_amount (optional, default 0)
                - due_date (optional, YYYY-MM-DD)

        Returns:
            Tuple (success, message).
        """
        # Validate required fields
        required = ['roll_no', 'academic_year', 'term', 'total_amount']
        for field in required:
            if field not in data or not str(data[field]).strip():
                return False, f"{field.replace('_', ' ').title()} is required."

        # Validate total amount
        try:
            total = float(data['total_amount'])
            if total <= 0:
                return False, "Total amount must be positive."
        except (ValueError, TypeError):
            return False, "Total amount must be a valid number."

        # Validate paid amount if provided
        paid = data.get('paid_amount', 0.0)
        if paid:
            try:
                paid = float(paid)
                if paid < 0:
                    return False, "Paid amount cannot be negative."
                if paid > total:
                    return False, "Paid amount cannot exceed total amount."
            except (ValueError, TypeError):
                return False, "Paid amount must be a valid number."
        else:
            paid = 0.0

        # Validate due date if provided
        due_date = data.get('due_date', '').strip()
        if due_date and not validate_date(due_date, "%Y-%m-%d"):
            return False, "Due date must be in YYYY-MM-DD format."

        # Prepare record
        record = {
            'roll_no': data['roll_no'].strip(),
            'academic_year': data['academic_year'].strip(),
            'term': data['term'].strip(),
            'total_amount': total,
            'paid_amount': paid,
            'due_date': due_date if due_date else None
        }

        if self.fees_model.insert_fee_structure(record):
            return True, "Fee structure added successfully."
        else:
            return False, "Failed to add fee structure. The combination may already exist."

    def update_fee_structure(self, fee_id: int, data: dict) -> tuple[bool, str]:
        """
        Update an existing fee structure.

        Args:
            fee_id: The fee record ID.
            data: Dictionary with fields to update (academic_year, term, total_amount, due_date).

        Returns:
            Tuple (success, message).
        """
        existing = self.fees_model.get_by_id(fee_id)
        if not existing:
            return False, "Fee structure not found."

        update_data = {}
        if 'academic_year' in data:
            update_data['academic_year'] = data['academic_year'].strip()
        if 'term' in data:
            update_data['term'] = data['term'].strip()
        if 'due_date' in data:
            date_str = data['due_date'].strip()
            if date_str and not validate_date(date_str, "%Y-%m-%d"):
                return False, "Due date must be in YYYY-MM-DD format."
            update_data['due_date'] = date_str if date_str else None
        if 'total_amount' in data:
            try:
                new_total = float(data['total_amount'])
                if new_total <= 0:
                    return False, "Total amount must be positive."
                if new_total < existing['paid_amount']:
                    return False, "Total amount cannot be less than already paid amount."
                update_data['total_amount'] = new_total
            except (ValueError, TypeError):
                return False, "Total amount must be a valid number."

        if not update_data:
            return False, "No fields to update."

        if self.fees_model.update_fee_structure(fee_id, update_data):
            return True, "Fee structure updated successfully."
        else:
            return False, "Failed to update fee structure."

    def delete_fee_structure(self, fee_id: int) -> tuple[bool, str]:
        """
        Delete a fee structure. Prevent deletion if payments have been made.

        Args:
            fee_id: The fee record ID.

        Returns:
            Tuple (success, message).
        """
        existing = self.fees_model.get_by_id(fee_id)
        if not existing:
            return False, "Fee structure not found."
        if existing['paid_amount'] > 0:
            return False, "Cannot delete a fee structure with recorded payments."

        if self.fees_model.delete_fee_structure(fee_id):
            return True, "Fee structure deleted successfully."
        else:
            return False, "Failed to delete fee structure."

    # ─────────────────────────────────────────────────────────────
    #  PAYMENT OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def record_payment(self, fee_id: int, amount: float) -> tuple[bool, str]:
        """
        Record a payment towards a fee structure.

        Args:
            fee_id: The fee record ID.
            amount: Payment amount (positive).

        Returns:
            Tuple (success, message).
        """
        if amount <= 0:
            return False, "Payment amount must be positive."

        existing = self.fees_model.get_by_id(fee_id)
        if not existing:
            return False, "Fee structure not found."

        current_paid = existing['paid_amount']
        total = existing['total_amount']

        # Allow overpayment but warn (handled by UI)
        new_paid = current_paid + amount

        if self.fees_model.record_payment(fee_id, new_paid):
            return True, f"Payment of ₹{amount:.2f} recorded successfully."
        else:
            return False, "Failed to record payment."

    def get_payment_status(self, fee_id: int) -> str:
        """
        Get payment status string for a fee record.

        Returns:
            'PAID', 'PARTIAL', 'UNPAID', or 'OVERDUE'.
        """
        record = self.fees_model.get_by_id(fee_id)
        if not record:
            return "UNKNOWN"

        due = record['total_amount'] - record['paid_amount']
        if due <= 0:
            return "PAID"
        elif record['paid_amount'] > 0:
            # Check overdue
            if record['due_date']:
                try:
                    due_date = datetime.strptime(record['due_date'], "%Y-%m-%d").date()
                    if due_date < datetime.now().date():
                        return "OVERDUE"
                except ValueError:
                    pass
            return "PARTIAL"
        else:
            if record['due_date']:
                try:
                    due_date = datetime.strptime(record['due_date'], "%Y-%m-%d").date()
                    if due_date < datetime.now().date():
                        return "OVERDUE"
                except ValueError:
                    pass
            return "UNPAID"

    # ─────────────────────────────────────────────────────────────
    #  QUERY METHODS
    # ─────────────────────────────────────────────────────────────
    def get_student_fees(self, roll_no: str) -> list:
        """
        Get all fee records for a student.

        Args:
            roll_no: Student roll number.

        Returns:
            List of fee dictionaries.
        """
        if not roll_no or not roll_no.strip():
            return []
        return self.fees_model.get_by_roll(roll_no.strip())

    def get_all_fees_with_names(self) -> list:
        """
        Get all fee records joined with student names.

        Returns:
            List of dictionaries with fee data and 'student_name'.
        """
        return self.fees_model.fetch_all_with_student_names()

    def get_fee_summary(self, roll_no: str) -> dict:
        """
        Get aggregated fee summary for a student.

        Returns:
            Dict with: total_fee, paid, due, status.
        """
        if not roll_no or not roll_no.strip():
            return {"total_fee": 0.0, "paid": 0.0, "due": 0.0, "status": "NO_STUDENT"}
        return self.fees_model.get_summary_by_roll(roll_no.strip())

    # ─────────────────────────────────────────────────────────────
    #  OVERDUE MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    def get_overdue_students(self) -> list:
        """
        Get list of students with overdue fees.

        Returns:
            List of dicts with roll_no, student_name, total_due.
        """
        return self.fees_model.get_overdue_students()

    def get_total_outstanding(self) -> float:
        """
        Get total outstanding due across all students.

        Returns:
            Float total amount due.
        """
        return self.fees_model.get_outstanding_total()