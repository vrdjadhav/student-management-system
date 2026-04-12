"""
Views Package
-------------
Contains all UI components of the Student Management System.
This file makes the package importable and exposes key view classes.
"""

# Convenience imports – allow users to write:
#   from views import MainWindow, StudentDashboard
# instead of:
#   from views.main_window import MainWindow

from .main_window import MainWindow
from .base_view import BaseView

# The following views will be implemented later; uncomment as they become available
# from .student_dashboard import StudentDashboard
# from .attendance_view import AttendanceView
# from .fees_view import FeesView
# from .exam_graphs_view import ExamGraphsView
# from .report_view import ReportView

__all__ = [
    "MainWindow",
    "BaseView",
    # "StudentDashboard",
    # "AttendanceView",
    # "FeesView",
    # "ExamGraphsView",
    # "ReportView",
]