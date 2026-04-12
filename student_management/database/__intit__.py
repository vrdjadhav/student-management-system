"""
Database Package
----------------
Contains the database connection manager and model classes for
students, attendance, fees, and exams.
"""

from .db_manager import DatabaseManager
from .student_model import StudentModel
from .attendance_model import AttendanceModel
from .fees_model import FeesModel
from .exam_model import ExamModel

__all__ = [
    "DatabaseManager",
    "StudentModel",
    "AttendanceModel",
    "FeesModel",
    "ExamModel",
]