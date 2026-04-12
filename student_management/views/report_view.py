"""
Report Generation View
----------------------
Provides a dialog to select a student and choose which sections
to include in a printable PDF report.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from views.base_view import BaseView
from utils.theme_manager import ThemeManager
from utils.pdf_generator import generate_student_report
from database.student_model import StudentModel
from config import Themes


class ReportView(BaseView):
    """Toplevel window for generating student reports."""

    def __init__(self, master, db_manager, roll_no=None):
        super().__init__(master)
        self.db_manager = db_manager
        self.student_model = StudentModel(db_manager)
        self.selected_roll = roll_no

        self.title("Generate Student Report")
        self.geometry("500x500")
        self.resizable(False, False)

        self._build_ui()
        self._load_students()

        if self.selected_roll:
            self._set_selected_student()

    # ─────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Create all UI components."""
        # Header
        header = tk.Frame(self, bg=self.get_color("header"))
        header.pack(fill="x")

        tk.Label(
            header,
            text="📄 Generate Student Report",
            font=("Segoe UI Semibold", 14),
            bg=self.get_color("header"),
            fg=self.get_color("header_text")
        ).pack(pady=12)

        # Main content frame
        content = tk.Frame(self, bg=self.get_color("panel"))
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Student selection
        tk.Label(
            content,
            text="Select Student:",
            font=("Segoe UI", 10, "bold"),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        ).pack(anchor="w", pady=(0, 5))

        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(
            content,
            textvariable=self.student_var,
            state="readonly",
            width=40,
            font=("Segoe UI", 10)
        )
        self.student_combo.pack(fill="x", pady=(0, 15))
        self.student_combo.bind("<<ComboboxSelected>>", self._on_student_selected)

        # Section selection frame
        section_frame = tk.LabelFrame(
            content,
            text="Report Sections",
            font=("Segoe UI", 10, "bold"),
            bg=self.get_color("panel"),
            fg=self.get_color("text"),
            padx=10, pady=10
        )
        section_frame.pack(fill="x", pady=(0, 15))

        # Checkbox variables
        self.include_personal = tk.BooleanVar(value=True)
        self.include_attendance = tk.BooleanVar(value=True)
        self.include_fees = tk.BooleanVar(value=True)
        self.include_exams = tk.BooleanVar(value=True)
        self.include_graphs = tk.BooleanVar(value=True)

        checkboxes = [
            ("Personal Details", self.include_personal),
            ("Attendance Summary", self.include_attendance),
            ("Fees Statement", self.include_fees),
            ("Exam Scores Table", self.include_exams),
            ("Performance Graphs", self.include_graphs),
        ]

        for text, var in checkboxes:
            cb = tk.Checkbutton(
                section_frame,
                text=text,
                variable=var,
                bg=self.get_color("panel"),
                fg=self.get_color("text"),
                selectcolor=self.get_color("panel"),
                activebackground=self.get_color("panel"),
                font=("Segoe UI", 10)
            )
            cb.pack(anchor="w", pady=2)

        # Report options
        options_frame = tk.LabelFrame(
            content,
            text="Options",
            font=("Segoe UI", 10, "bold"),
            bg=self.get_color("panel"),
            fg=self.get_color("text"),
            padx=10, pady=10
        )
        options_frame.pack(fill="x", pady=(0, 15))

        self.include_charts_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Include charts in PDF",
            variable=self.include_charts_var,
            bg=self.get_color("panel"),
            fg=self.get_color("text"),
            selectcolor=self.get_color("panel"),
            activebackground=self.get_color("panel"),
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=2)

        # Generate button
        self.generate_btn = tk.Button(
            content,
            text="📄 Generate Report",
            bg=self.get_color("add_btn"),
            fg="white",
            font=("Segoe UI Semibold", 11),
            relief="flat",
            cursor="hand2",
            padx=20, pady=8,
            command=self._generate_report
        )
        self.generate_btn.pack(pady=10)
        self.generate_btn.config(state="disabled")  # Enable only when student selected

        # Status label
        self.status_var = tk.StringVar(value="Select a student to continue.")
        status_label = tk.Label(
            content,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=self.get_color("panel"),
            fg=self.get_color("label")
        )
        status_label.pack(pady=(5, 0))

        # Apply theme colors
        self._apply_theme_colors()

    # ─────────────────────────────────────────────────────────────
    #  DATA LOADING
    # ─────────────────────────────────────────────────────────────
    def _load_students(self):
        """Load all students into the combobox."""
        students = self.student_model.fetch_all()
        self.student_list = [f"{s['Roll_No']} - {s['Name']}" for s in students]
        self.student_combo["values"] = self.student_list

    def _set_selected_student(self):
        """Preselect the student if roll_no was provided."""
        for item in self.student_list:
            if item.startswith(self.selected_roll + " -"):
                self.student_var.set(item)
                self.generate_btn.config(state="normal")
                self.status_var.set(f"Ready to generate report for {self.selected_roll}")
                break

    def _on_student_selected(self, event=None):
        """Enable generate button when a student is selected."""
        if self.student_var.get():
            self.selected_roll = self.student_var.get().split(" - ")[0]
            self.generate_btn.config(state="normal")
            self.status_var.set(f"Ready to generate report for {self.selected_roll}")
        else:
            self.generate_btn.config(state="disabled")
            self.status_var.set("Select a student to continue.")

    # ─────────────────────────────────────────────────────────────
    #  REPORT GENERATION
    # ─────────────────────────────────────────────────────────────
    def _generate_report(self):
        """Collect options, call PDF generator, and save file."""
        if not self.selected_roll:
            messagebox.showwarning("No Student", "Please select a student first.")
            return

        # Build options dict
        options = {
            "include_personal": self.include_personal.get(),
            "include_attendance": self.include_attendance.get(),
            "include_fees": self.include_fees.get(),
            "include_exams": self.include_exams.get(),
            "include_graphs": self.include_graphs.get(),
            "include_charts": self.include_charts_var.get(),
        }

        # Ask for save location
        default_filename = f"Report_{self.selected_roll}_{self._get_current_date_str()}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Save Report As"
        )
        if not filepath:
            return

        # Disable button during generation
        self.generate_btn.config(state="disabled", text="⏳ Generating...")
        self.status_var.set("Generating report, please wait...")
        self.update_idletasks()

        try:
            # Call the PDF generator utility
            success = generate_student_report(
                db_manager=self.db_manager,
                roll_no=self.selected_roll,
                output_path=filepath,
                options=options
            )
            if success:
                messagebox.showinfo("Success", f"Report saved to:\n{filepath}")
                self.status_var.set("Report generated successfully.")
            else:
                messagebox.showerror("Error", "Failed to generate report.")
                self.status_var.set("Report generation failed.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_var.set("Error generating report.")
        finally:
            self.generate_btn.config(state="normal", text="📄 Generate Report")

    def _get_current_date_str(self):
        """Return current date as YYYYMMDD string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d")

    # ─────────────────────────────────────────────────────────────
    #  THEME HANDLING
    # ─────────────────────────────────────────────────────────────
    def _apply_theme_colors(self):
        """Apply theme colours to custom widgets."""
        theme = self._theme
        self.configure(bg=theme["bg"])
        # Children will be updated by base class or recursion

    def on_theme_change(self, theme_dict):
        """Called when the application theme changes."""
        self._apply_theme_colors()
        self._apply_theme_to_children(self)

    def _apply_theme_to_children(self, widget):
        """Recursively apply background colours."""
        theme = self._theme
        if isinstance(widget, (tk.Frame, tk.LabelFrame)):
            try:
                widget.configure(bg=theme["panel"])
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Label) and not isinstance(widget, ttk.Label):
            try:
                widget.configure(bg=theme["panel"], fg=theme["text"])
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Checkbutton):
            try:
                widget.configure(bg=theme["panel"], fg=theme["text"])
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._apply_theme_to_children(child)