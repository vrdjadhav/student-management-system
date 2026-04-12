"""
Utilities Package
-----------------
Helper modules for validation, Excel handling, PDF generation,
theme management, and other common tasks.
"""

# Convenience imports
from .validators import validate_email, validate_phone, validate_date
from .theme_manager import ThemeManager
from .excel_handler import parse_attendance_excel
from .pdf_generator import generate_fee_receipt, generate_student_report

__all__ = [
    "validate_email",
    "validate_phone",
    "validate_date",
    "ThemeManager",
    "parse_attendance_excel",
    "generate_fee_receipt",
    "generate_student_report",
]