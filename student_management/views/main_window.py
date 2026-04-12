"""
Main Application Window
-----------------------
The central hub of the Student Management System.
Contains the student CRUD interface, records table, and navigation to other modules.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re

from views.base_view import BaseFrame
from utils.theme_manager import ThemeManager
from utils.validators import validate_email, validate_phone, validate_date
from database.student_model import StudentModel
from config import Themes, STUDENT_COLUMNS, STUDENT_COLUMN_WIDTHS, STUDENT_FORM_FIELDS


class MainWindow(BaseFrame):
    """Main application frame containing student management UI."""

    def __init__(self, master, db_manager):
        super().__init__(master)
        self.db_manager = db_manager
        self.student_model = StudentModel(db_manager)
        self._sort_reverse = {}

        self._setup_ui()
        self._refresh_table()
        self._build_menu()

    # ─────────────────────────────────────────────────────────────
    #  UI SETUP
    # ─────────────────────────────────────────────────────────────
    def _setup_ui(self):
        """Build the complete UI layout."""
        self._build_header()
        self._build_body()

    def _build_header(self):
        """Create the top header bar with title and clock."""
        hdr = tk.Frame(self, bg=self.get_color("header"), height=60)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="🎓  Student Management System",
            font=("Segoe UI Semibold", 18),
            bg=self.get_color("header"),
            fg=self.get_color("header_text")
        ).pack(side="left", padx=24, pady=10)

        # Theme toggle button (🌙/☀️)
        self.theme_btn = tk.Button(
            hdr,
            text="🌙 Dark Mode",
            bg=self.get_color("accent"),
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=10, pady=3,
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="right", padx=10)

        # Live clock
        self._clock_var = tk.StringVar()
        tk.Label(
            hdr,
            textvariable=self._clock_var,
            font=("Segoe UI", 10),
            bg=self.get_color("header"),
            fg="#90CAF9"
        ).pack(side="right", padx=20)
        self._tick()

    def _tick(self):
        """Update the live clock every second."""
        self._clock_var.set(datetime.now().strftime("%a, %d %b %Y   %H:%M:%S"))
        self.after(1000, self._tick)

    def _toggle_theme(self):
        """Switch between light and dark themes."""
        new_theme = "dark" if ThemeManager._current_theme == "light" else "light"
        ThemeManager.apply_theme(new_theme, self.winfo_toplevel())
        self.theme_btn.config(text="☀️ Light Mode" if new_theme == "dark" else "🌙 Dark Mode")

    def _build_body(self):
        """Create the two‑column layout: left form panel and right records panel."""
        body = tk.Frame(self, bg=self.get_color("bg"))
        body.pack(fill="both", expand=True, padx=12, pady=10)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_manage_panel(body)
        self._build_records_panel(body)

    # ─────────────────────────────────────────────────────────────
    #  LEFT PANEL: STUDENT FORM
    # ─────────────────────────────────────────────────────────────
    def _build_manage_panel(self, parent):
        """Build the left panel with student input form and action buttons."""
        left = tk.Frame(
            parent,
            bg=self.get_color("panel"),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.get_color("border")
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.config(width=310)
        left.grid_propagate(False)

        # Title bar
        tk.Label(
            left,
            text="Manage Student",
            font=("Segoe UI Semibold", 13),
            bg=self.get_color("accent"),
            fg="white",
            padx=12, pady=8
        ).pack(fill="x")

        # Form frame
        form = tk.Frame(left, bg=self.get_color("panel"))
        form.pack(fill="both", expand=True, padx=18, pady=10)

        self._vars = {}
        self._inputs = {}

        for idx, (label, key, wtype, opts) in enumerate(STUDENT_FORM_FIELDS):
            # Label
            tk.Label(
                form,
                text=label,
                font=("Segoe UI", 10),
                bg=self.get_color("panel"),
                fg=self.get_color("label"),
                anchor="w"
            ).grid(row=idx * 2, column=0, sticky="w", pady=(8, 1))

            if wtype == "text":
                txt = tk.Text(
                    form,
                    height=3,
                    width=28,
                    font=("Segoe UI", 10),
                    bg=self.get_color("entry_bg"),
                    fg=self.get_color("text"),
                    relief="solid",
                    bd=1,
                    wrap="word"
                )
                txt.grid(row=idx * 2 + 1, column=0, sticky="ew", pady=(0, 2))
                self._inputs[key] = txt
            else:
                var = tk.StringVar()
                self._vars[key] = var
                if wtype == "combo":
                    w = ttk.Combobox(
                        form,
                        textvariable=var,
                        values=opts,
                        state="readonly",
                        font=("Segoe UI", 10)
                    )
                else:
                    w = ttk.Entry(form, textvariable=var, font=("Segoe UI", 10))
                    if key == "dob":
                        var.set("DD/MM/YYYY")
                        w.bind("<FocusIn>", lambda e, v=var: v.set("") if v.get() == "DD/MM/YYYY" else None)
                        w.bind("<FocusOut>", lambda e, v=var: v.set("DD/MM/YYYY") if v.get() == "" else None)
                w.grid(row=idx * 2 + 1, column=0, sticky="ew", pady=(0, 2))
                self._inputs[key] = w

            form.columnconfigure(0, weight=1)

        # Button row
        btn_frame = tk.Frame(left, bg=self.get_color("panel"))
        btn_frame.pack(fill="x", padx=18, pady=(4, 14))

        buttons = [
            ("➕  Add",    self.get_color("add_btn"), self.get_color("add_hover"), self._add_student),
            ("✏️  Update", self.get_color("upd_btn"), self.get_color("upd_hover"), self._update_student),
            ("🗑  Delete",  self.get_color("del_btn"), self.get_color("del_hover"), self._delete_student),
            ("✖  Clear",   self.get_color("clr_btn"), self.get_color("clr_hover"), self._clear_fields),
        ]

        for col, (text, color, hover_color, cmd) in enumerate(buttons):
            btn = self._make_button(btn_frame, text, color, hover_color, cmd)
            btn.grid(row=col // 2, column=col % 2, padx=4, pady=4, sticky="ew")
            btn_frame.columnconfigure(col % 2, weight=1)

        # Quick navigation buttons to other modules
        nav_frame = tk.Frame(left, bg=self.get_color("panel"))
        nav_frame.pack(fill="x", padx=18, pady=(0, 14))

        tk.Label(
            nav_frame,
            text="Quick Access",
            font=("Segoe UI", 9, "bold"),
            bg=self.get_color("panel"),
            fg=self.get_color("label")
        ).pack(anchor="w", pady=(0, 5))

        nav_buttons = [
            ("📋 Attendance", self._open_attendance),
            ("💰 Fees", self._open_fees),
            ("📊 Dashboard", self._open_dashboard),
        ]
        for text, cmd in nav_buttons:
            btn = tk.Button(
                nav_frame,
                text=text,
                bg=self.get_color("accent"),
                fg="white",
                font=("Segoe UI", 9),
                relief="flat",
                cursor="hand2",
                padx=5, pady=4,
                command=cmd
            )
            btn.pack(fill="x", pady=2)

    def _make_button(self, parent, text, bg, hover_bg, cmd):
        """Factory: create a styled tk.Button with hover effect."""
        btn = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg="white",
            activebackground=hover_bg,
            activeforeground="white",
            font=("Segoe UI Semibold", 10),
            relief="flat",
            cursor="hand2",
            padx=6, pady=7,
            command=cmd
        )
        btn.bind("<Enter>", lambda e, b=btn, h=hover_bg: b.config(bg=h))
        btn.bind("<Leave>", lambda e, b=btn, n=bg: b.config(bg=n))
        return btn

    # ─────────────────────────────────────────────────────────────
    #  RIGHT PANEL: RECORDS TABLE + SEARCH
    # ─────────────────────────────────────────────────────────────
    def _build_records_panel(self, parent):
        """Build the right panel with student records Treeview and search bar."""
        right = tk.Frame(
            parent,
            bg=self.get_color("panel"),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.get_color("border")
        )
        right.grid(row=0, column=1, sticky="nsew")

        # Top bar with title and search
        top = tk.Frame(right, bg=self.get_color("accent"))
        top.pack(fill="x")

        tk.Label(
            top,
            text="Student Records",
            font=("Segoe UI Semibold", 13),
            bg=self.get_color("accent"),
            fg="white",
            padx=12, pady=8
        ).pack(side="left")

        # Search widgets
        self._search_var = tk.StringVar()
        self._search_field = tk.StringVar(value="Name")

        search_frame = tk.Frame(top, bg=self.get_color("accent"))
        search_frame.pack(side="right", padx=12, pady=6)

        ttk.Combobox(
            search_frame,
            textvariable=self._search_field,
            values=["Roll_No", "Name"],
            state="readonly",
            width=8,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 4))

        ttk.Entry(
            search_frame,
            textvariable=self._search_var,
            font=("Segoe UI", 10),
            width=20
        ).pack(side="left")

        search_btn = tk.Button(
            search_frame,
            text="🔍",
            bg=self.get_color("upd_btn"),
            fg="white",
            activebackground=self.get_color("upd_hover"),
            font=("Segoe UI", 11),
            relief="flat",
            cursor="hand2",
            padx=6, pady=2,
            command=self._search
        )
        search_btn.pack(side="left", padx=(4, 0))

        reset_btn = tk.Button(
            search_frame,
            text="↺",
            bg=self.get_color("clr_btn"),
            fg="white",
            activebackground=self.get_color("clr_hover"),
            font=("Segoe UI", 12),
            relief="flat",
            cursor="hand2",
            padx=6, pady=2,
            command=self._reset_search
        )
        reset_btn.pack(side="left", padx=(4, 0))

        # Count label
        self._count_var = tk.StringVar(value="0 records")
        tk.Label(
            right,
            textvariable=self._count_var,
            font=("Segoe UI", 9, "italic"),
            bg=self.get_color("panel"),
            fg="#9E9E9E",
            anchor="e",
            padx=10
        ).pack(fill="x", side="bottom")

        # Treeview + scrollbars
        tree_frame = tk.Frame(right, bg=self.get_color("panel"))
        tree_frame.pack(fill="both", expand=True, padx=8, pady=(6, 2))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=STUDENT_COLUMNS,
            show="headings",
            style="Custom.Treeview",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse"
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, width in zip(STUDENT_COLUMNS, STUDENT_COLUMN_WIDTHS):
            self.tree.heading(
                col,
                text=col.replace("_", " "),
                command=lambda c=col: self._sort_column(c)
            )
            self.tree.column(col, width=width, anchor="center", minwidth=60)

        self.tree.tag_configure("odd", background=self.get_color("row_odd"))
        self.tree.tag_configure("even", background=self.get_color("row_even"))

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ─────────────────────────────────────────────────────────────
    #  MENU BAR
    # ─────────────────────────────────────────────────────────────
    def _build_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.winfo_toplevel())
        self.winfo_toplevel().config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.winfo_toplevel().quit)

        # Modules menu
        modules_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Modules", menu=modules_menu)
        modules_menu.add_command(label="📋 Attendance Management", command=self._open_attendance)
        modules_menu.add_command(label="💰 Fees Management", command=self._open_fees)
        modules_menu.add_command(label="📊 Exam Graphs", command=self._open_exam_graphs)
        modules_menu.add_separator()
        modules_menu.add_command(label="📄 Student Dashboard", command=self._open_dashboard)
        modules_menu.add_command(label="🖨️ Printable Report", command=self._open_report)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    # ─────────────────────────────────────────────────────────────
    #  FORM DATA HANDLING
    # ─────────────────────────────────────────────────────────────
    def _get_form_data(self):
        """Collect and validate all form inputs. Returns dict or None."""
        data = {}
        for key, widget in self._inputs.items():
            if isinstance(widget, tk.Text):
                val = widget.get("1.0", "end-1c").strip()
            else:
                val = self._vars[key].get().strip()

            if not val or val == "DD/MM/YYYY":
                messagebox.showwarning("Validation", f"Field '{key.replace('_',' ')}' cannot be empty.")
                return None
            data[key.capitalize() if key != "roll_no" else "Roll_No"] = val

        # Additional validation
        if not validate_email(data.get("Email", "")):
            messagebox.showwarning("Validation", "Invalid email address.")
            return None
        if not validate_phone(data.get("Contact", "")):
            messagebox.showwarning("Validation", "Contact must be 10 digits.")
            return None
        if not validate_date(data.get("Dob", "")):
            messagebox.showwarning("Validation", "Date must be DD/MM/YYYY.")
            return None

        return {
            "Roll_No": data["Roll_No"],
            "Name": data["Name"],
            "Email": data["Email"],
            "Gender": data["Gender"],
            "Contact": data["Contact"],
            "DOB": data["Dob"],
            "Address": data["Address"],
        }

    def _populate_form(self, row):
        """Fill the form with data from the selected row."""
        mapping = {
            "roll_no": "Roll_No",
            "name": "Name",
            "email": "Email",
            "gender": "Gender",
            "contact": "Contact",
            "dob": "DOB",
        }
        for key, col in mapping.items():
            widget = self._inputs[key]
            if isinstance(widget, ttk.Combobox):
                self._vars[key].set(row.get(col, ""))
            else:
                self._vars[key].set(row.get(col, ""))

        txt = self._inputs["address"]
        txt.delete("1.0", "end")
        txt.insert("1.0", row.get("Address", ""))

    def _clear_fields(self):
        """Reset all form fields to default/empty."""
        for key, widget in self._inputs.items():
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
            elif isinstance(widget, ttk.Combobox):
                self._vars[key].set("")
            else:
                self._vars[key].set("DD/MM/YYYY" if key == "dob" else "")

    # ─────────────────────────────────────────────────────────────
    #  CRUD OPERATIONS
    # ─────────────────────────────────────────────────────────────
    def _add_student(self):
        data = self._get_form_data()
        if data is None:
            return
        if self.student_model.insert(data):
            self._refresh_table()
            self._clear_fields()
            messagebox.showinfo("Success", "Student added successfully.")

    def _update_student(self):
        if not self.tree.selection():
            messagebox.showwarning("No Selection", "Please select a row to update.")
            return
        data = self._get_form_data()
        if data is None:
            return
        if self.student_model.update(data):
            self._refresh_table()
            self._clear_fields()
            messagebox.showinfo("Success", "Record updated successfully.")
        else:
            messagebox.showerror("Error", "Update failed. Record may not exist.")

    def _delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a row to delete.")
            return
        roll = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Permanently delete student '{roll}'?"):
            if self.student_model.delete(roll):
                self._refresh_table()
                self._clear_fields()
                messagebox.showinfo("Deleted", "Record removed successfully.")

    # ─────────────────────────────────────────────────────────────
    #  TREEVIEW HELPERS
    # ─────────────────────────────────────────────────────────────
    def _refresh_table(self, rows=None):
        """Clear and reload the Treeview."""
        self.tree.delete(*self.tree.get_children())
        data = rows if rows is not None else self.student_model.fetch_all()
        for i, row in enumerate(data):
            tag = "odd" if i % 2 else "even"
            self.tree.insert(
                "",
                "end",
                values=[row[c] for c in STUDENT_COLUMNS],
                tags=(tag,)
            )
        self._count_var.set(f"{len(data)} record{'s' if len(data) != 1 else ''}")

    def _on_row_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        row = dict(zip(STUDENT_COLUMNS, vals))
        self._populate_form(row)

    def _sort_column(self, col):
        """Toggle‑sort the Treeview by the clicked column."""
        rev = self._sort_reverse.get(col, False)
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(reverse=rev, key=lambda t: t[0].lower() if isinstance(t[0], str) else t[0])
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
            self.tree.item(k, tags=("odd" if index % 2 else "even",))
        self._sort_reverse[col] = not rev

    def _search(self):
        field = self._search_field.get()
        value = self._search_var.get().strip()
        if not value:
            messagebox.showwarning("Search", "Enter a search term.")
            return
        results = self.student_model.search(field, value)
        self._refresh_table(results)

    def _reset_search(self):
        self._search_var.set("")
        self._refresh_table()

    # ─────────────────────────────────────────────────────────────
    #  MODULE NAVIGATION
    # ─────────────────────────────────────────────────────────────
    def _open_attendance(self):
        from views.attendance_view import AttendanceView
        AttendanceView(self.winfo_toplevel(), self.db_manager)

    def _open_fees(self):
        from views.fees_view import FeesView
        FeesView(self.winfo_toplevel(), self.db_manager)

    def _open_exam_graphs(self):
        from views.exam_graphs_view import ExamGraphsView
        ExamGraphsView(self.winfo_toplevel(), self.db_manager)

    def _open_dashboard(self):
        sel = self.tree.selection()
        if sel:
            roll_no = self.tree.item(sel[0], "values")[0]
        else:
            roll_no = None
        from views.student_dashboard import StudentDashboard
        StudentDashboard(self.winfo_toplevel(), self.db_manager, roll_no)

    def _open_report(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a student to generate a report.")
            return
        roll_no = self.tree.item(sel[0], "values")[0]
        from views.report_view import ReportView
        ReportView(self.winfo_toplevel(), self.db_manager, roll_no)

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "Student Management System\nVersion 2.0\n\n"
            "A comprehensive solution for managing students,\n"
            "attendance, fees, exams, and reports.\n\n"
            "© 2026 All Rights Reserved."
        )

    # ─────────────────────────────────────────────────────────────
    #  THEME HANDLING
    # ─────────────────────────────────────────────────────────────
    def on_theme_change(self, theme_dict):
        """Update custom widget colours when theme changes."""
        # Update header background
        for child in self.winfo_children():
            if isinstance(child, tk.Frame) and child.winfo_height() == 60:
                child.configure(bg=theme_dict["header"])
                break

        # Update form panel colours
        self._apply_theme_to_children(self)

        # Update tree row tags
        self.tree.tag_configure("odd", background=theme_dict["row_odd"])
        self.tree.tag_configure("even", background=theme_dict["row_even"])

        # Refresh table to reapply tags
        self._refresh_table()

    def _apply_theme_to_children(self, widget):
        """Recursively apply theme colours to custom tk widgets."""
        theme = self._theme
        if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame, tk.LabelFrame)):
            try:
                widget.configure(bg=theme["bg"])
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            if isinstance(child, (tk.Frame, tk.LabelFrame)):
                try:
                    child.configure(bg=theme["panel"])
                except tk.TclError:
                    pass
            elif isinstance(child, tk.Label) and not isinstance(child, ttk.Label):
                try:
                    child.configure(bg=theme["panel"], fg=theme["text"])
                except tk.TclError:
                    pass
            elif isinstance(child, tk.Text):
                try:
                    child.configure(bg=theme["entry_bg"], fg=theme["text"])
                except tk.TclError:
                    pass
            if child.winfo_children():
                self._apply_theme_to_children(child)