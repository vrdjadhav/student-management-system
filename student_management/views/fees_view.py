"""
Fees Management View
--------------------
Provides UI for managing student fees, recording payments,
tracking dues, and generating receipts.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os

from views.base_view import BaseView
from utils.theme_manager import ThemeManager
from utils.pdf_generator import generate_fee_receipt
from database.fees_model import FeesModel
from database.student_model import StudentModel
from config import Themes


class FeesView(BaseView):
    """Toplevel window for fee operations."""

    def __init__(self, master, db_manager):
        super().__init__(master)
        self.db_manager = db_manager
        self.fees_model = FeesModel(db_manager)
        self.student_model = StudentModel(db_manager)

        self.title("Fees Management")
        self.geometry("1050x700")
        self.minsize(900, 600)

        # Data containers
        self.students = []
        self.fee_records = []

        self._build_ui()
        self._load_students()
        self._load_all_fees()

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
            text="💰 Fees Management",
            font=("Segoe UI Semibold", 16),
            bg=self.get_color("header"),
            fg=self.get_color("header_text")
        ).pack(side="left", padx=20, pady=10)

        # Toolbar
        toolbar = tk.Frame(self, bg=self.get_color("panel"))
        toolbar.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Button(
            toolbar, text="➕ Add Fee Structure",
            command=self._open_add_fee_dialog
        ).pack(side="left", padx=5)

        ttk.Button(
            toolbar, text="💵 Record Payment",
            command=self._open_payment_dialog
        ).pack(side="left", padx=5)

        ttk.Button(
            toolbar, text="📄 Generate Receipt",
            command=self._generate_receipt
        ).pack(side="left", padx=5)

        ttk.Button(
            toolbar, text="🔄 Refresh",
            command=self._load_all_fees
        ).pack(side="left", padx=5)

        # Search bar
        search_frame = tk.Frame(toolbar, bg=self.get_color("panel"))
        search_frame.pack(side="right", padx=5)

        tk.Label(
            search_frame, text="🔍",
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        ).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_tree())
        ttk.Entry(
            search_frame, textvariable=self.search_var, width=20
        ).pack(side="left", padx=5)

        # Main content: Treeview of fee records
        tree_frame = tk.Frame(self, bg=self.get_color("panel"))
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Roll_No", "Name", "Term", "Total", "Paid", "Due", "Status", "Due_Date")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        # Define headings
        self.tree.heading("Roll_No", text="Roll No")
        self.tree.heading("Name", text="Student Name")
        self.tree.heading("Term", text="Term")
        self.tree.heading("Total", text="Total (₹)")
        self.tree.heading("Paid", text="Paid (₹)")
        self.tree.heading("Due", text="Due (₹)")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Due_Date", text="Due Date")

        # Set column widths
        self.tree.column("Roll_No", width=80, anchor="center")
        self.tree.column("Name", width=180, anchor="w")
        self.tree.column("Term", width=100, anchor="center")
        self.tree.column("Total", width=100, anchor="e")
        self.tree.column("Paid", width=100, anchor="e")
        self.tree.column("Due", width=100, anchor="e")
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Due_Date", width=100, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Configure tags for status highlighting
        self.tree.tag_configure("paid", background="#C8E6C9")      # green
        self.tree.tag_configure("partial", background="#FFF9C4")   # yellow
        self.tree.tag_configure("unpaid", background="#FFCDD2")    # red
        self.tree.tag_configure("overdue", background="#EF9A9A")   # dark red

        # Bind double-click to view/edit
        self.tree.bind("<Double-1>", self._on_item_double_click)

        # Summary panel at bottom
        summary_frame = tk.Frame(self, bg=self.get_color("panel"), height=60)
        summary_frame.pack(fill="x", padx=10, pady=(0, 10))
        summary_frame.pack_propagate(False)

        self.summary_label = tk.Label(
            summary_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        )
        self.summary_label.pack(pady=15)

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

        # Apply theme colours
        self._apply_theme_colors()

    # ─────────────────────────────────────────────────────────────
    #  DATA LOADING
    # ─────────────────────────────────────────────────────────────
    def _load_students(self):
        """Load all students for dropdowns."""
        self.students = self.student_model.fetch_all()

    def _load_all_fees(self):
        """Load all fee records and display in treeview."""
        self.tree.delete(*self.tree.get_children())
        self.fee_records = self.fees_model.fetch_all_with_student_names()

        total_due = 0.0
        for rec in self.fee_records:
            due = rec["total_amount"] - rec["paid_amount"]
            total_due += due

            status, tag = self._get_status_info(rec)
            due_date = rec.get("due_date", "N/A")

            self.tree.insert(
                "",
                "end",
                values=(
                    rec["roll_no"],
                    rec.get("student_name", "Unknown"),
                    rec["term"],
                    f"{rec['total_amount']:.2f}",
                    f"{rec['paid_amount']:.2f}",
                    f"{due:.2f}",
                    status,
                    due_date
                ),
                tags=(tag,)
            )

        self._update_summary(len(self.fee_records), total_due)
        self.status_var.set(f"Loaded {len(self.fee_records)} fee records")

    def _get_status_info(self, rec):
        """Determine status string and tag based on payment and due date."""
        due = rec["total_amount"] - rec["paid_amount"]
        due_date_str = rec.get("due_date")

        if due <= 0:
            return "PAID", "paid"
        elif due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                if due_date < datetime.now().date():
                    return "OVERDUE", "overdue"
                else:
                    return "UNPAID", "unpaid"
            except ValueError:
                return "UNPAID", "unpaid"
        else:
            return "PARTIAL", "partial"

    def _update_summary(self, count, total_due):
        """Update the summary label with totals."""
        self.summary_label.config(
            text=f"Total Fee Records: {count}   |   Total Outstanding: ₹{total_due:,.2f}"
        )

    def _filter_tree(self):
        """Filter tree rows based on search text (roll number or name)."""
        query = self.search_var.get().strip().lower()
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            roll = str(values[0]).lower()
            name = str(values[1]).lower()
            if query in roll or query in name:
                self.tree.reattach(child, "", "end")
            else:
                self.tree.detach(child)

    # ─────────────────────────────────────────────────────────────
    #  DIALOGS: ADD FEE STRUCTURE
    # ─────────────────────────────────────────────────────────────
    def _open_add_fee_dialog(self):
        """Open dialog to add a new fee structure for a student."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Fee Structure")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.configure(bg=self.get_color("panel"))
        dialog.transient(self)
        dialog.grab_set()

        # Form fields
        fields = [
            ("Student", "combo"),
            ("Term", "entry"),
            ("Total Amount (₹)", "entry"),
            ("Due Date (YYYY-MM-DD)", "entry")
        ]

        entries = {}
        row = 0
        for label, ftype in fields:
            tk.Label(
                dialog, text=label + ":",
                bg=self.get_color("panel"),
                fg=self.get_color("text"),
                font=("Segoe UI", 10)
            ).grid(row=row, column=0, sticky="e", padx=10, pady=8)

            if ftype == "combo":
                var = tk.StringVar()
                student_list = [f"{s['Roll_No']} - {s['Name']}" for s in self.students]
                w = ttk.Combobox(dialog, textvariable=var, values=student_list, state="readonly", width=25)
                w.grid(row=row, column=1, sticky="w", padx=10, pady=8)
                entries["student"] = var
            else:
                var = tk.StringVar()
                w = ttk.Entry(dialog, textvariable=var, width=27)
                w.grid(row=row, column=1, sticky="w", padx=10, pady=8)
                key = label.lower().replace(" ", "_").replace("(₹)", "amount").replace("(", "").replace(")", "")
                entries[key] = var
            row += 1

        # Academic Year (optional)
        tk.Label(
            dialog, text="Academic Year:",
            bg=self.get_color("panel"),
            fg=self.get_color("text"),
            font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky="e", padx=10, pady=8)
        year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Entry(dialog, textvariable=year_var, width=27).grid(row=row, column=1, sticky="w", padx=10, pady=8)
        entries["academic_year"] = year_var

        def save_fee_structure():
            # Validate
            student_sel = entries["student"].get()
            if not student_sel:
                messagebox.showwarning("Validation", "Please select a student.")
                return
            roll_no = student_sel.split(" - ")[0]

            term = entries.get("term", tk.StringVar()).get().strip()
            if not term:
                messagebox.showwarning("Validation", "Term is required.")
                return

            try:
                total = float(entries.get("total_amount", tk.StringVar()).get())
                if total <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Validation", "Total amount must be a positive number.")
                return

            due_date = entries.get("due_date", tk.StringVar()).get().strip()
            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Validation", "Due date must be in YYYY-MM-DD format.")
                    return

            academic_year = year_var.get().strip() or str(datetime.now().year)

            # Insert into database
            data = {
                "roll_no": roll_no,
                "academic_year": academic_year,
                "term": term,
                "total_amount": total,
                "paid_amount": 0.0,
                "due_date": due_date if due_date else None
            }
            if self.fees_model.insert_fee_structure(data):
                messagebox.showinfo("Success", "Fee structure added.")
                self._load_all_fees()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to add fee structure.")

        btn_frame = tk.Frame(dialog, bg=self.get_color("panel"))
        btn_frame.grid(row=row+1, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=save_fee_structure).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=10)

    # ─────────────────────────────────────────────────────────────
    #  DIALOGS: RECORD PAYMENT
    # ─────────────────────────────────────────────────────────────
    def _open_payment_dialog(self):
        """Open dialog to record a payment against a selected fee record."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a fee record first.")
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        roll_no = values[0]
        term = values[2]
        total = float(values[3])
        paid = float(values[4])
        due = float(values[5])

        # Find the fee record ID
        fee_id = None
        for rec in self.fee_records:
            if rec["roll_no"] == roll_no and rec["term"] == term:
                fee_id = rec["id"]
                break

        if fee_id is None:
            messagebox.showerror("Error", "Could not locate fee record.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Record Payment")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.configure(bg=self.get_color("panel"))
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(
            dialog, text=f"Student: {roll_no} - {values[1]}",
            bg=self.get_color("panel"), fg=self.get_color("text"),
            font=("Segoe UI", 11, "bold")
        ).pack(pady=10)

        tk.Label(
            dialog, text=f"Term: {term}   |   Total: ₹{total:.2f}   |   Paid: ₹{paid:.2f}",
            bg=self.get_color("panel"), fg=self.get_color("text"),
            font=("Segoe UI", 10)
        ).pack()

        tk.Label(
            dialog, text=f"Outstanding Due: ₹{due:.2f}",
            bg=self.get_color("panel"), fg="#C62828",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=5)

        # Payment amount entry
        frame = tk.Frame(dialog, bg=self.get_color("panel"))
        frame.pack(pady=15)

        tk.Label(
            frame, text="Payment Amount (₹):",
            bg=self.get_color("panel"), fg=self.get_color("text")
        ).pack(side="left", padx=5)

        amount_var = tk.StringVar()
        ttk.Entry(frame, textvariable=amount_var, width=15).pack(side="left", padx=5)

        def record_payment():
            try:
                amt = float(amount_var.get())
                if amt <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Validation", "Enter a valid positive amount.")
                return

            if amt > due:
                if not messagebox.askyesno("Overpayment",
                                           f"Amount ₹{amt:.2f} exceeds due ₹{due:.2f}. Continue anyway?"):
                    return

            # Record payment
            payment_date = datetime.now().strftime("%Y-%m-%d")
            new_paid = paid + amt
            success = self.fees_model.record_payment(fee_id, new_paid, payment_date)

            if success:
                messagebox.showinfo("Success", f"Payment of ₹{amt:.2f} recorded.")
                self._load_all_fees()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to record payment.")

        btn_frame = tk.Frame(dialog, bg=self.get_color("panel"))
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Record Payment", command=record_payment).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=10)

    # ─────────────────────────────────────────────────────────────
    #  GENERATE RECEIPT
    # ─────────────────────────────────────────────────────────────
    def _generate_receipt(self):
        """Generate a PDF receipt for the selected fee record."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a fee record.")
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        roll_no = values[0]
        term = values[2]

        # Find full record
        fee_record = None
        for rec in self.fee_records:
            if rec["roll_no"] == roll_no and rec["term"] == term:
                fee_record = rec
                break

        if not fee_record:
            messagebox.showerror("Error", "Could not retrieve fee details.")
            return

        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"Receipt_{roll_no}_{term}.pdf"
        )
        if not filepath:
            return

        try:
            generate_fee_receipt(fee_record, filepath)
            messagebox.showinfo("Receipt Generated", f"Receipt saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"Could not generate receipt:\n{e}")

    # ─────────────────────────────────────────────────────────────
    #  DOUBLE-CLICK TO EDIT
    # ─────────────────────────────────────────────────────────────
    def _on_item_double_click(self, event):
        """Allow editing of fee structure (e.g., change due date)."""
        selection = self.tree.selection()
        if not selection:
            return
        # For simplicity, just open payment dialog or edit dialog
        # Could implement an edit dialog similar to add dialog
        self._open_payment_dialog()

    # ─────────────────────────────────────────────────────────────
    #  THEME HANDLING
    # ─────────────────────────────────────────────────────────────
    def _apply_theme_colors(self):
        """Apply theme colours to custom widgets."""
        theme = self._theme
        self.configure(bg=theme["bg"])
        self.summary_label.configure(bg=theme["panel"], fg=theme["text"])

        # Update tree tags with theme-appropriate colours
        if ThemeManager._current_theme == "dark":
            self.tree.tag_configure("paid", background="#2E7D32")
            self.tree.tag_configure("partial", background="#F9A825")
            self.tree.tag_configure("unpaid", background="#C62828")
            self.tree.tag_configure("overdue", background="#B71C1C")
        else:
            self.tree.tag_configure("paid", background="#C8E6C9")
            self.tree.tag_configure("partial", background="#FFF9C4")
            self.tree.tag_configure("unpaid", background="#FFCDD2")
            self.tree.tag_configure("overdue", background="#EF9A9A")

    def on_theme_change(self, theme_dict):
        """Called when the application theme changes."""
        self._apply_theme_colors()