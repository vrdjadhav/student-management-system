"""
Attendance Management View
--------------------------
Provides UI for viewing, marking, and importing student attendance.
Supports Excel upload, manual entry, and summary statistics.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os

from views.base_view import BaseView
from utils.theme_manager import ThemeManager
from utils.excel_handler import parse_attendance_excel
from database.attendance_model import AttendanceModel
from database.student_model import StudentModel
from config import Themes


class AttendanceView(BaseView):
    """Toplevel window for attendance operations."""

    def __init__(self, master, db_manager):
        super().__init__(master)
        self.db_manager = db_manager
        self.attendance_model = AttendanceModel(db_manager)
        self.student_model = StudentModel(db_manager)

        self.title("Attendance Management")
        self.geometry("1000x650")
        self.minsize(800, 500)

        # Current date context (default: today)
        self.selected_date = datetime.now().date()

        self._build_ui()
        self._load_attendance_data()

    # ─────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Create all UI components."""
        # Header with title and date selector
        header_frame = tk.Frame(self, bg=self._get_theme_color("header"))
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text="📋 Attendance Management",
            font=("Segoe UI Semibold", 16),
            bg=self._get_theme_color("header"),
            fg=self._get_theme_color("header_text")
        ).pack(side="left", padx=20, pady=10)

        # Date navigation
        date_frame = tk.Frame(header_frame, bg=self._get_theme_color("header"))
        date_frame.pack(side="right", padx=20, pady=10)

        ttk.Button(
            date_frame, text="◀", width=3,
            command=self._prev_day
        ).pack(side="left", padx=2)

        self.date_label = tk.Label(
            date_frame,
            text=self.selected_date.strftime("%A, %d %B %Y"),
            font=("Segoe UI", 11),
            bg=self._get_theme_color("header"),
            fg=self._get_theme_color("header_text"),
            width=25
        )
        self.date_label.pack(side="left", padx=10)

        ttk.Button(
            date_frame, text="▶", width=3,
            command=self._next_day
        ).pack(side="left", padx=2)

        ttk.Button(
            date_frame, text="📅 Today", width=8,
            command=self._goto_today
        ).pack(side="left", padx=10)

        # Toolbar
        toolbar = tk.Frame(self, bg=self._get_theme_color("panel"))
        toolbar.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Button(
            toolbar, text="📤 Import Excel",
            command=self._import_excel
        ).pack(side="left", padx=5)

        ttk.Button(
            toolbar, text="💾 Save Changes",
            command=self._save_changes
        ).pack(side="left", padx=5)

        ttk.Button(
            toolbar, text="📊 View Summary",
            command=self._show_summary
        ).pack(side="left", padx=5)

        # Search in attendance grid
        search_frame = tk.Frame(toolbar, bg=self._get_theme_color("panel"))
        search_frame.pack(side="right", padx=5)

        tk.Label(
            search_frame, text="🔍",
            bg=self._get_theme_color("panel"),
            fg=self._get_theme_color("text")
        ).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_grid())
        ttk.Entry(
            search_frame, textvariable=self.search_var, width=20
        ).pack(side="left", padx=5)

        # Main content area with grid and summary side panel
        content = tk.Frame(self, bg=self._get_theme_color("panel"))
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Attendance grid (Treeview with checkboxes simulation)
        grid_frame = tk.Frame(content, bg=self._get_theme_color("panel"))
        grid_frame.pack(side="left", fill="both", expand=True)

        # Create Treeview for attendance marking
        columns = ("Roll_No", "Name", "Status")
        self.tree = ttk.Treeview(
            grid_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse",
            height=15
        )

        self.tree.heading("Roll_No", text="Roll No")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Status", text="Status")

        self.tree.column("Roll_No", width=100, anchor="center")
        self.tree.column("Name", width=200, anchor="w")
        self.tree.column("Status", width=120, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.rowconfigure(0, weight=1)

        # Bind double-click to cycle status
        self.tree.bind("<Double-1>", self._on_status_click)

        # Right: Summary panel
        summary_panel = tk.Frame(
            content,
            bg=self._get_theme_color("panel"),
            width=200,
            highlightthickness=1,
            highlightbackground=self._get_theme_color("border")
        )
        summary_panel.pack(side="right", fill="y", padx=(10, 0))
        summary_panel.pack_propagate(False)

        tk.Label(
            summary_panel,
            text="Summary",
            font=("Segoe UI Semibold", 12),
            bg=self._get_theme_color("accent"),
            fg="white",
            pady=8
        ).pack(fill="x")

        self.summary_text = tk.Text(
            summary_panel,
            height=15,
            width=25,
            bg=self._get_theme_color("entry_bg"),
            fg=self._get_theme_color("text"),
            font=("Segoe UI", 10),
            relief="flat",
            borderwidth=0,
            wrap="word",
            state="disabled"
        )
        self.summary_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken",
            bg=self._get_theme_color("accent"),
            fg="white"
        )
        status_bar.pack(fill="x", side="bottom")

        # Apply initial theme colours
        self._apply_theme_colors()

    # ─────────────────────────────────────────────────────────────
    #  DATA LOADING & DISPLAY
    # ─────────────────────────────────────────────────────────────
    def _load_attendance_data(self):
        """Fetch students and their attendance for the selected date."""
        self.tree.delete(*self.tree.get_children())

        # Get all students
        students = self.student_model.fetch_all()
        if not students:
            return

        # Get existing attendance records for the date
        date_str = self.selected_date.strftime("%Y-%m-%d")
        records = self.attendance_model.get_by_date(date_str)
        attendance_map = {rec["roll_no"]: rec["status"] for rec in records}

        # Populate tree
        for i, student in enumerate(students):
            roll = student["Roll_No"]
            name = student["Name"]
            status = attendance_map.get(roll, "Absent")  # default absent
            tag = "odd" if i % 2 else "even"
            self.tree.insert(
                "",
                "end",
                values=(roll, name, status),
                tags=(tag, status.lower())
            )

        # Configure tags for status colors
        self.tree.tag_configure("present", background="#C8E6C9")
        self.tree.tag_configure("absent", background="#FFCDD2")
        self.tree.tag_configure("late", background="#FFF9C4")

        self._update_summary()
        self.status_var.set(f"Loaded {len(students)} students for {date_str}")

    def _update_summary(self):
        """Update the summary panel with attendance statistics."""
        total = 0
        present = 0
        absent = 0
        late = 0

        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            if len(values) >= 3:
                total += 1
                status = values[2]
                if status == "Present":
                    present += 1
                elif status == "Absent":
                    absent += 1
                elif status == "Late":
                    late += 1

        summary = (
            f"Date: {self.selected_date.strftime('%d/%m/%Y')}\n"
            f"{'─'*20}\n"
            f"Total Students: {total}\n"
            f"Present: {present} ({self._pct(present, total)}%)\n"
            f"Absent:  {absent} ({self._pct(absent, total)}%)\n"
            f"Late:    {late} ({self._pct(late, total)}%)\n"
        )

        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary)
        self.summary_text.config(state="disabled")

    @staticmethod
    def _pct(part, whole):
        return round((part / whole) * 100, 1) if whole else 0

    def _filter_grid(self):
        """Filter tree rows based on search entry."""
        query = self.search_var.get().strip().lower()
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            if not values:
                continue
            roll = str(values[0]).lower()
            name = str(values[1]).lower()
            if query in roll or query in name:
                self.tree.reattach(child, "", "end")
            else:
                self.tree.detach(child)

    # ─────────────────────────────────────────────────────────────
    #  STATUS TOGGLING (Double‑click)
    # ─────────────────────────────────────────────────────────────
    def _on_status_click(self, event):
        """Cycle status: Absent → Present → Late → Absent."""
        item = self.tree.selection()[0]
        current = self.tree.item(item, "values")[2]
        cycle = {"Absent": "Present", "Present": "Late", "Late": "Absent"}
        new_status = cycle.get(current, "Absent")

        values = list(self.tree.item(item, "values"))
        values[2] = new_status
        self.tree.item(item, values=values, tags=(self.tree.item(item, "tags")[0], new_status.lower()))
        self._update_summary()

    # ─────────────────────────────────────────────────────────────
    #  SAVE CHANGES
    # ─────────────────────────────────────────────────────────────
    def _save_changes(self):
        """Save all attendance statuses to the database."""
        date_str = self.selected_date.strftime("%Y-%m-%d")
        records = []
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            roll = values[0]
            status = values[2]
            records.append((roll, date_str, status))

        if self.attendance_model.bulk_upsert(records):
            messagebox.showinfo("Success", f"Attendance saved for {date_str}")
            self._load_attendance_data()
        else:
            messagebox.showerror("Error", "Failed to save attendance.")

    # ─────────────────────────────────────────────────────────────
    #  DATE NAVIGATION
    # ─────────────────────────────────────────────────────────────
    def _prev_day(self):
        self.selected_date -= timedelta(days=1)
        self.date_label.config(text=self.selected_date.strftime("%A, %d %B %Y"))
        self._load_attendance_data()

    def _next_day(self):
        self.selected_date += timedelta(days=1)
        self.date_label.config(text=self.selected_date.strftime("%A, %d %B %Y"))
        self._load_attendance_data()

    def _goto_today(self):
        self.selected_date = datetime.now().date()
        self.date_label.config(text=self.selected_date.strftime("%A, %d %B %Y"))
        self._load_attendance_data()

    # ─────────────────────────────────────────────────────────────
    #  EXCEL IMPORT
    # ─────────────────────────────────────────────────────────────
    def _import_excel(self):
        """Open file dialog, parse Excel, preview, and import."""
        filepath = filedialog.askopenfilename(
            title="Select Attendance Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            records = parse_attendance_excel(filepath)
        except Exception as e:
            messagebox.showerror("Parse Error", f"Could not read Excel file:\n{e}")
            return

        if not records:
            messagebox.showwarning("No Data", "No attendance records found in the file.")
            return

        # Preview dialog
        preview = tk.Toplevel(self)
        preview.title("Import Preview")
        preview.geometry("600x400")
        preview.configure(bg=self._get_theme_color("panel"))

        tk.Label(
            preview,
            text=f"Found {len(records)} attendance records. Import?",
            font=("Segoe UI", 11),
            bg=self._get_theme_color("panel"),
            fg=self._get_theme_color("text")
        ).pack(pady=10)

        # Preview tree
        tree_frame = tk.Frame(preview)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Roll_No", "Date", "Status")
        preview_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        for col in cols:
            preview_tree.heading(col, text=col)
            preview_tree.column(col, width=100)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=preview_tree.yview)
        preview_tree.configure(yscrollcommand=vsb.set)
        preview_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for rec in records[:50]:  # show first 50
            preview_tree.insert("", "end", values=(rec["Roll_No"], rec["Date"], rec["Status"]))

        # Buttons
        btn_frame = tk.Frame(preview, bg=self._get_theme_color("panel"))
        btn_frame.pack(pady=10)

        def do_import():
            success = self.attendance_model.bulk_upsert_from_dicts(records)
            preview.destroy()
            if success:
                self._load_attendance_data()
                messagebox.showinfo("Import Complete", f"Imported {len(records)} records.")
            else:
                messagebox.showerror("Import Failed", "Some records could not be imported.")

        ttk.Button(btn_frame, text="Import", command=do_import).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=preview.destroy).pack(side="left", padx=10)

    # ─────────────────────────────────────────────────────────────
    #  SUMMARY REPORT
    # ─────────────────────────────────────────────────────────────
    def _show_summary(self):
        """Show a monthly summary report in a new window."""
        summary_win = tk.Toplevel(self)
        summary_win.title("Monthly Attendance Summary")
        summary_win.geometry("700x500")
        summary_win.configure(bg=self._get_theme_color("panel"))

        # Fetch data for current month
        year = self.selected_date.year
        month = self.selected_date.month
        summary = self.attendance_model.get_monthly_summary(year, month)

        # Display using Treeview
        cols = ("Roll_No", "Name", "Present", "Absent", "Late", "Total", "Percentage")
        tree = ttk.Treeview(summary_win, columns=cols, show="headings")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")

        for row in summary:
            total = row["Present"] + row["Absent"] + row["Late"]
            pct = (row["Present"] / total * 100) if total else 0
            tree.insert("", "end", values=(
                row["Roll_No"],
                row["Name"],
                row["Present"],
                row["Absent"],
                row["Late"],
                total,
                f"{pct:.1f}%"
            ))

    # ─────────────────────────────────────────────────────────────
    #  THEME HANDLING
    # ─────────────────────────────────────────────────────────────
    def _get_theme_color(self, key):
        """Get the current theme colour by key."""
        theme = Themes.LIGHT if ThemeManager._current_theme == "light" else Themes.DARK
        return theme.get(key, "#FFFFFF")

    def _apply_theme_colors(self):
        """Apply theme colours to custom widgets."""
        theme = Themes.LIGHT if ThemeManager._current_theme == "light" else Themes.DARK

        self.configure(bg=theme["bg"])
        self.summary_text.configure(bg=theme["entry_bg"], fg=theme["text"])

        # Update header children
        for child in self.winfo_children():
            if isinstance(child, tk.Frame) and child.winfo_children():
                # Recursively update background of frames
                pass  # Not fully implemented for brevity; theme observer will handle.

    def on_theme_change(self, theme):
        """Called when ThemeManager switches themes."""
        self._apply_theme_colors()
        # Reapply row tags with new colours
        self.tree.tag_configure("present", background="#C8E6C9" if theme == Themes.LIGHT else "#2E7D32")
        self.tree.tag_configure("absent", background="#FFCDD2" if theme == Themes.LIGHT else "#C62828")
        self.tree.tag_configure("late", background="#FFF9C4" if theme == Themes.LIGHT else "#F9A825")