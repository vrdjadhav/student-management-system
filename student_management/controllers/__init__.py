"""
Controllers Package
------------------
Contains the business logic controllers that mediate between views and models.
"""

# Import controllers as they are implemented
from .student_controller import StudentController
from .attendance_controller import AttendanceController
from .fees_controller import FeesController
from .exam_controller import ExamController

__all__ = [
    "StudentController",
    "AttendanceController",
    "FeesController",
    "ExamController",
]