"""
Student Dashboard View
----------------------
Displays aggregated information for a single student in a clean,
card‑based layout with quick access to related modules.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from views.base_view import BaseView
from utils.theme_manager import ThemeManager
from database.student_model import StudentModel
from database.attendance_model import AttendanceModel
from database.fees_model import FeesModel
from database.exam_model import ExamModel
from config import Themes


class StudentDashboard(BaseView):
    """Toplevel window showing a student's complete overview."""

    def __init__(self, master, db_manager, roll_no=None):
        super().__init__(master)
        self.db_manager = db_manager
        self.student_model = StudentModel(db_manager)
        self.attendance_model = AttendanceModel(db_manager)
        self.fees_model = FeesModel(db_manager)
        self.exam_model = ExamModel(db_manager)

        self.selected_roll = roll_no
        self.student_data = None

        self.title("Student Dashboard")
        self.geometry("900x650")
        self.minsize(800, 550)

        self._build_ui()
        self._load_students()

        if self.selected_roll:
            self._load_dashboard_data()
        else:
            # Show a prompt to select a student
            self._show_selection_prompt()

    # ─────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Create the dashboard layout."""
        # Header
        header = tk.Frame(self, bg=self.get_color("header"), height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="👤 Student Dashboard",
            font=("Segoe UI Semibold", 16),
            bg=self.get_color("header"),
            fg=self.get_color("header_text")
        ).pack(side="left", padx=20, pady=10)

        # Student selector (only shown if no preselected student)
        self.selector_frame = tk.Frame(header, bg=self.get_color("header"))
        self.selector_frame.pack(side="right", padx=20)

        tk.Label(
            self.selector_frame,
            text="Select Student:",
            font=("Segoe UI", 10),
            bg=self.get_color("header"),
            fg=self.get_color("header_text")
        ).pack(side="left", padx=(0, 5))

        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(
            self.selector_frame,
            textvariable=self.student_var,
            state="readonly",
            width=25,
            font=("Segoe UI", 10)
        )
        self.student_combo.pack(side="left")
        self.student_combo.bind("<<ComboboxSelected>>", self._on_student_selected)

        # Main content area (scrollable)
        canvas = tk.Canvas(self, bg=self.get_color("bg"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.get_color("bg"))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Dashboard content will be built dynamically after data load
        self.content_frame = tk.Frame(self.scrollable_frame, bg=self.get_color("bg"))
        self.content_frame.pack(fill="both", expand=True)

        # Show placeholder
        self.placeholder_label = tk.Label(
            self.content_frame,
            text="Select a student to view dashboard",
            font=("Segoe UI", 12),
            bg=self.get_color("bg"),
            fg=self.get_color("text")
        )
        self.placeholder_label.pack(pady=50)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken",
            bg=self.get_color("accent"),
            fg="white"
        )
        status_bar.pack(fill="x", side="bottom")

    # ─────────────────────────────────────────────────────────────
    #  DATA LOADING
    # ─────────────────────────────────────────────────────────────
    def _load_students(self):
        """Populate the student dropdown."""
        students = self.student_model.fetch_all()
        self.student_list = [f"{s['Roll_No']} - {s['Name']}" for s in students]
        self.student_combo["values"] = self.student_list

        # If roll_no provided, set selection
        if self.selected_roll:
            for i, s in enumerate(students):
                if s["Roll_No"] == self.selected_roll:
                    self.student_combo.current(i)
                    break

    def _show_selection_prompt(self):
        """Display a message prompting student selection."""
        self.placeholder_label.config(text="Please select a student from the dropdown above.")

    def _on_student_selected(self, event=None):
        """Handle student selection from combobox."""
        selection = self.student_var.get()
        if not selection:
            return
        self.selected_roll = selection.split(" - ")[0]
        self._load_dashboard_data()

    def _load_dashboard_data(self):
        """Fetch all necessary data for the selected student."""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Fetch student details
        self.student_data = self.student_model.get_by_roll(self.selected_roll)
        if not self.student_data:
            messagebox.showerror("Error", f"Student {self.selected_roll} not found.")
            return

        # Fetch summary data
        attendance_summary = self.attendance_model.get_summary_by_roll(self.selected_roll)
        fees_summary = self.fees_model.get_summary_by_roll(self.selected_roll)
        recent_exams = self.exam_model.get_recent_by_roll(self.selected_roll, limit=5)

        # Build dashboard UI
        self._build_personal_card()
        self._build_attendance_card(attendance_summary)
        self._build_fees_card(fees_summary)
        self._build_exams_card(recent_exams)
        self._build_action_buttons()

        self.status_var.set(f"Dashboard loaded for {self.student_data['Name']} ({self.selected_roll})")

    # ─────────────────────────────────────────────────────────────
    #  DASHBOARD CARDS
    # ─────────────────────────────────────────────────────────────
    def _build_personal_card(self):
        """Create the personal information card."""
        card = self._create_card("Personal Information")
        data = self.student_data

        info_text = (
            f"Roll No:     {data['Roll_No']}\n"
            f"Full Name:   {data['Name']}\n"
            f"Email:       {data['Email']}\n"
            f"Gender:      {data['Gender']}\n"
            f"Contact:     {data['Contact']}\n"
            f"Date of Birth: {data['DOB']}\n"
            f"Address:     {data['Address']}"
        )

        tk.Label(
            card,
            text=info_text,
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text"),
            justify="left"
        ).pack(anchor="w", padx=15, pady=10)

    def _build_attendance_card(self, summary):
        """Create the attendance summary card."""
        card = self._create_card("Attendance Summary")

        total = summary.get("total_days", 0)
        present = summary.get("present", 0)
        absent = summary.get("absent", 0)
        late = summary.get("late", 0)
        percentage = summary.get("percentage", 0)

        text = (
            f"Total Days Recorded: {total}\n"
            f"Present: {present}   Absent: {absent}   Late: {late}\n"
            f"Attendance Percentage: {percentage:.1f}%"
        )

        tk.Label(
            card,
            text=text,
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        ).pack(anchor="w", padx=15, pady=10)

        # Progress bar for attendance percentage
        progress_frame = tk.Frame(card, bg=self.get_color("panel"))
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))

        bar_canvas = tk.Canvas(
            progress_frame,
            height=15,
            bg=self.get_color("entry_bg"),
            highlightthickness=0
        )
        bar_canvas.pack(fill="x")

        bar_width = 300
        fill_width = int((percentage / 100) * bar_width) if total > 0 else 0
        bar_canvas.create_rectangle(0, 0, fill_width, 15, fill=self.get_color("add_btn"), width=0)

    def _build_fees_card(self, summary):
        """Create the fees summary card."""
        card = self._create_card("Fees Status")

        total_fee = summary.get("total_fee", 0.0)
        paid = summary.get("paid", 0.0)
        due = summary.get("due", 0.0)
        status = summary.get("status", "Unknown")

        text = (
            f"Total Fees:   ₹{total_fee:,.2f}\n"
            f"Paid Amount:  ₹{paid:,.2f}\n"
            f"Due Amount:   ₹{due:,.2f}\n"
            f"Status:       {status}"
        )

        tk.Label(
            card,
            text=text,
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        ).pack(anchor="w", padx=15, pady=10)

        # Status color indicator
        status_colors = {
            "PAID": self.get_color("add_btn"),
            "PARTIAL": "#F9A825",
            "UNPAID": self.get_color("del_btn"),
            "OVERDUE": "#B71C1C"
        }
        color = status_colors.get(status, self.get_color("text"))
        tk.Label(
            card,
            text="●",
            font=("Segoe UI", 16),
            bg=self.get_color("panel"),
            fg=color
        ).place(relx=0.9, rely=0.2)

    def _build_exams_card(self, exams):
        """Create the recent exam scores card."""
        card = self._create_card("Recent Exam Scores")

        if not exams:
            tk.Label(
                card,
                text="No exam records found.",
                font=("Segoe UI", 10, "italic"),
                bg=self.get_color("panel"),
                fg=self.get_color("label")
            ).pack(anchor="w", padx=15, pady=10)
            return

        # Table header
        header_frame = tk.Frame(card, bg=self.get_color("accent"))
        header_frame.pack(fill="x", padx=10, pady=(10, 0))

        headers = ["Subject", "Marks", "Percentage", "Date"]
        for i, h in enumerate(headers):
            tk.Label(
                header_frame,
                text=h,
                font=("Segoe UI Semibold", 9),
                bg=self.get_color("accent"),
                fg="white",
                width=12 if i < 2 else 10
            ).grid(row=0, column=i, padx=1)

        # Data rows
        for idx, exam in enumerate(exams):
            row_bg = self.get_color("row_odd") if idx % 2 else self.get_color("row_even")
            row_frame = tk.Frame(card, bg=row_bg)
            row_frame.pack(fill="x", padx=10)

            marks = f"{exam['marks_obtained']:.1f}/{exam['max_marks']:.1f}"
            pct = (exam['marks_obtained'] / exam['max_marks'] * 100) if exam['max_marks'] else 0
            date = exam.get('exam_date', 'N/A')

            tk.Label(
                row_frame,
                text=exam['subject'],
                width=12,
                bg=row_bg,
                fg=self.get_color("text"),
                font=("Segoe UI", 9)
            ).grid(row=0, column=0)

            tk.Label(
                row_frame,
                text=marks,
                width=12,
                bg=row_bg,
                fg=self.get_color("text"),
                font=("Segoe UI", 9)
            ).grid(row=0, column=1)

            tk.Label(
                row_frame,
                text=f"{pct:.1f}%",
                width=10,
                bg=row_bg,
                fg=self.get_color("text"),
                font=("Segoe UI", 9)
            ).grid(row=0, column=2)

            tk.Label(
                row_frame,
                text=date,
                width=10,
                bg=row_bg,
                fg=self.get_color("text"),
                font=("Segoe UI", 9)
            ).grid(row=0, column=3)

    def _build_action_buttons(self):
        """Create quick action buttons."""
        card = self._create_card("Quick Actions")

        btn_frame = tk.Frame(card, bg=self.get_color("panel"))
        btn_frame.pack(pady=10)

        actions = [
            ("📋 View Attendance", self._open_attendance),
            ("💰 Manage Fees", self._open_fees),
            ("📊 Exam Graphs", self._open_exam_graphs),
            ("📄 Generate Report", self._open_report),
        ]

        for text, cmd in actions:
            btn = tk.Button(
                btn_frame,
                text=text,
                bg=self.get_color("accent"),
                fg="white",
                font=("Segoe UI", 10),
                relief="flat",
                cursor="hand2",
                padx=15, pady=5,
                command=cmd
            )
            btn.pack(side="left", padx=5)

    def _create_card(self, title):
        """Helper to create a styled card frame with title."""
        card = tk.Frame(
            self.content_frame,
            bg=self.get_color("panel"),
            highlightthickness=1,
            highlightbackground=self.get_color("border")
        )
        card.pack(fill="x", padx=5, pady=5)

        title_label = tk.Label(
            card,
            text=title,
            font=("Segoe UI Semibold", 11),
            bg=self.get_color("accent"),
            fg="white",
            padx=10, pady=5
        )
        title_label.pack(fill="x")

        return card

    # ─────────────────────────────────────────────────────────────
    #  QUICK ACTIONS
    # ─────────────────────────────────────────────────────────────
    def _open_attendance(self):
        from views.attendance_view import AttendanceView
        AttendanceView(self.master, self.db_manager)

    def _open_fees(self):
        from views.fees_view import FeesView
        FeesView(self.master, self.db_manager)

    def _open_exam_graphs(self):
        from views.exam_graphs_view import ExamGraphsView
        ExamGraphsView(self.master, self.db_manager, self.selected_roll)

    def _open_report(self):
        from views.report_view import ReportView
        ReportView(self.master, self.db_manager, self.selected_roll)

    # ─────────────────────────────────────────────────────────────
    #  THEME HANDLING
    # ─────────────────────────────────────────────────────────────
    def on_theme_change(self, theme_dict):
        """Update colors when theme changes."""
        self._theme = theme_dict
        self.configure(bg=theme_dict["bg"])
        self.scrollable_frame.configure(bg=theme_dict["bg"])
        self.content_frame.configure(bg=theme_dict["bg"])
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.configure(bg=theme_dict["bg"], fg=theme_dict["text"])
        # Reload dashboard to refresh colors if data loaded
        if self.selected_roll and self.student_data:
            self._load_dashboard_data()