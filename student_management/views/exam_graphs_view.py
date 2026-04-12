"""
Exam Graphs View

Displays graphical representations of student exam scores.
Includes subject-wise bar charts and performance trend lines.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime

from views.base_view import BaseView
from utils.theme_manager import ThemeManager
from database.exam_model import ExamModel
from database.student_model import StudentModel
from config import Themes


class ExamGraphsView(BaseView):
    """Toplevel window for viewing exam performance graphs."""

    def __init__(self, master, db_manager, roll_no=None):
        """
        Initialize the exam graphs view.

        Args:
            master: Parent widget.
            db_manager: DatabaseManager instance.
            roll_no: Optional pre-selected student roll number.
        """
        super().__init__(master)
        self.db_manager = db_manager
        self.exam_model = ExamModel(db_manager)
        self.student_model = StudentModel(db_manager)
        self.selected_roll = roll_no

        self.title("Exam Performance Graphs")
        self.geometry("950x700")
        self.minsize(800, 600)

        # Data containers
        self.students = []
        self.exam_data = []
        self.subjects = []

        self._build_ui()
        self._load_students()
        if self.selected_roll:
            self._on_student_selected()

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
            text="📊 Exam Performance Graphs",
            font=("Segoe UI Semibold", 16),
            bg=self.get_color("header"),
            fg=self.get_color("header_text")
        ).pack(side="left", padx=20, pady=10)

        # Control bar (student selection, graph type)
        control_frame = tk.Frame(self, bg=self.get_color("panel"))
        control_frame.pack(fill="x", padx=10, pady=10)

        # Student selection
        tk.Label(
            control_frame,
            text="Select Student:",
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        ).pack(side="left", padx=(0, 5))

        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(
            control_frame,
            textvariable=self.student_var,
            state="readonly",
            width=25,
            font=("Segoe UI", 10)
        )
        self.student_combo.pack(side="left", padx=(0, 20))
        self.student_combo.bind("<<ComboboxSelected>>", self._on_student_selected)

        # Graph type toggle
        tk.Label(
            control_frame,
            text="Graph Type:",
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        ).pack(side="left", padx=(0, 5))

        self.graph_type = tk.StringVar(value="Subject-wise")
        graph_combo = ttk.Combobox(
            control_frame,
            textvariable=self.graph_type,
            values=["Subject-wise", "Trend Over Time"],
            state="readonly",
            width=18,
            font=("Segoe UI", 10)
        )
        graph_combo.pack(side="left", padx=(0, 20))
        graph_combo.bind("<<ComboboxSelected>>", self._on_graph_type_changed)

        # Refresh button
        ttk.Button(
            control_frame,
            text="🔄 Refresh",
            command=self._refresh_graph
        ).pack(side="left", padx=5)

        # Export button (save graph as image)
        ttk.Button(
            control_frame,
            text="💾 Save as PNG",
            command=self._export_graph
        ).pack(side="right", padx=5)

        # Main content area (matplotlib figure)
        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Subject selection panel (only visible for trend graph)
        self.subject_panel = tk.Frame(self, bg=self.get_color("panel"))
        self.subject_label = tk.Label(
            self.subject_panel,
            text="Select Subject:",
            font=("Segoe UI", 10),
            bg=self.get_color("panel"),
            fg=self.get_color("text")
        )
        self.subject_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(
            self.subject_panel,
            textvariable=self.subject_var,
            state="readonly",
            width=20,
            font=("Segoe UI", 10)
        )
        self.subject_combo.bind("<<ComboboxSelected>>", self._refresh_graph)

        # Initially hidden; will be shown when Trend graph is selected
        self.subject_panel.pack_forget()

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

        # Apply initial theme colors
        self._apply_theme_colors()

    # ─────────────────────────────────────────────────────────────
    #  DATA LOADING
    # ─────────────────────────────────────────────────────────────
    def _load_students(self):
        """Load all students into the combobox."""
        self.students = self.student_model.fetch_all()
        student_list = [f"{s['Roll_No']} - {s['Name']}" for s in self.students]
        self.student_combo["values"] = student_list

        if self.selected_roll:
            # Find and set the combobox value
            for i, s in enumerate(self.students):
                if s["Roll_No"] == self.selected_roll:
                    self.student_combo.current(i)
                    break

    def _load_exam_data(self):
        """Fetch exam records for the selected student."""
        if not self.selected_roll:
            return
        self.exam_data = self.exam_model.get_by_roll(self.selected_roll)
        self.subjects = sorted(list({rec["subject"] for rec in self.exam_data}))

        if not self.exam_data:
            self.status_var.set(f"No exam records found for {self.selected_roll}")

    # ─────────────────────────────────────────────────────────────
    #  EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────
    def _on_student_selected(self, event=None):
        """Handle student selection change."""
        selection = self.student_var.get()
        if not selection:
            return
        self.selected_roll = selection.split(" - ")[0]
        self._load_exam_data()
        self._update_subject_combo()
        self._refresh_graph()

    def _on_graph_type_changed(self, event=None):
        """Show/hide subject panel based on graph type."""
        if self.graph_type.get() == "Trend Over Time":
            self.subject_panel.pack(fill="x", padx=10, pady=(0, 5))
            self.subject_label.pack(side="left", padx=(0, 5))
            self.subject_combo.pack(side="left")
            self._update_subject_combo()
        else:
            self.subject_panel.pack_forget()
        self._refresh_graph()

    def _update_subject_combo(self):
        """Populate subject combobox with available subjects."""
        self.subject_combo["values"] = self.subjects
        if self.subjects:
            self.subject_combo.current(0)

    def _refresh_graph(self):
        """Redraw the graph based on current selections."""
        if not self.selected_roll:
            messagebox.showwarning("No Selection", "Please select a student first.")
            return

        self._load_exam_data()
        graph_type = self.graph_type.get()

        if graph_type == "Subject-wise":
            self._draw_subject_bar_chart()
        else:
            subject = self.subject_var.get()
            if not subject:
                messagebox.showinfo("Info", "Please select a subject for the trend graph.")
                return
            self._draw_trend_line(subject)

    # ─────────────────────────────────────────────────────────────
    #  GRAPH DRAWING
    # ─────────────────────────────────────────────────────────────
    def _draw_subject_bar_chart(self):
        """Draw a bar chart showing average/aggregate scores per subject."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if not self.exam_data:
            ax.text(0.5, 0.5, "No exam data available",
                    ha='center', va='center', fontsize=12)
            self.canvas.draw()
            self.status_var.set("No data to display")
            return

        # Aggregate data: average percentage per subject
        subject_scores = {}
        for rec in self.exam_data:
            subj = rec["subject"]
            pct = (rec["marks_obtained"] / rec["max_marks"]) * 100 if rec["max_marks"] else 0
            if subj not in subject_scores:
                subject_scores[subj] = []
            subject_scores[subj].append(pct)

        subjects = sorted(subject_scores.keys())
        averages = [sum(subject_scores[s]) / len(subject_scores[s]) for s in subjects]

        # Apply theme-appropriate colors
        is_dark = ThemeManager._current_theme == "dark"
        bar_color = self.get_color("accent")
        text_color = self.get_color("text")
        bg_color = self.get_color("panel")

        ax.set_facecolor(bg_color)
        self.fig.patch.set_facecolor(bg_color)

        bars = ax.bar(subjects, averages, color=bar_color, alpha=0.8)
        ax.set_xlabel("Subject", color=text_color)
        ax.set_ylabel("Average Percentage (%)", color=text_color)
        ax.set_title(f"Subject-wise Performance - {self.selected_roll}",
                     color=text_color, fontweight="bold")
        ax.set_ylim(0, 100)
        ax.tick_params(colors=text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)

        # Add value labels on bars
        for bar, avg in zip(bars, averages):
            height = bar.get_height()
            ax.annotate(f'{avg:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        color=text_color, fontsize=9)

        self.fig.tight_layout()
        self.canvas.draw()
        self.status_var.set(f"Displaying subject-wise averages for {self.selected_roll}")

    def _draw_trend_line(self, subject):
        """Draw a line chart showing performance over time for a specific subject."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Filter data for selected subject and sort by date
        subject_data = [rec for rec in self.exam_data if rec["subject"] == subject]
        if not subject_data:
            ax.text(0.5, 0.5, f"No exam data for {subject}",
                    ha='center', va='center', fontsize=12)
            self.canvas.draw()
            self.status_var.set(f"No data for {subject}")
            return

        # Sort by exam date
        subject_data.sort(key=lambda x: x.get("exam_date", ""))

        dates = [rec.get("exam_date", "Unknown") for rec in subject_data]
        scores = [(rec["marks_obtained"] / rec["max_marks"]) * 100 for rec in subject_data]

        is_dark = ThemeManager._current_theme == "dark"
        line_color = self.get_color("add_btn")  # greenish
        text_color = self.get_color("text")
        bg_color = self.get_color("panel")

        ax.set_facecolor(bg_color)
        self.fig.patch.set_facecolor(bg_color)

        ax.plot(dates, scores, marker='o', linestyle='-', linewidth=2,
                markersize=8, color=line_color)
        ax.set_xlabel("Exam Date", color=text_color)
        ax.set_ylabel("Percentage (%)", color=text_color)
        ax.set_title(f"Performance Trend - {subject} ({self.selected_roll})",
                     color=text_color, fontweight="bold")
        ax.set_ylim(0, 100)
        ax.tick_params(colors=text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)

        # Rotate date labels for readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        self.fig.tight_layout()
        self.canvas.draw()
        self.status_var.set(f"Displaying trend for {subject}")

    # ─────────────────────────────────────────────────────────────
    #  EXPORT FUNCTIONALITY
    # ─────────────────────────────────────────────────────────────
    def _export_graph(self):
        """Save the current figure as a PNG image."""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All files", "*.*")],
            title="Save Graph As"
        )
        if filepath:
            try:
                self.fig.savefig(filepath, dpi=150, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Graph saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    # ─────────────────────────────────────────────────────────────
    #  THEME HANDLING
    # ─────────────────────────────────────────────────────────────
    def _apply_theme_colors(self):
        """Apply current theme colours to custom widgets."""
        theme = self._theme
        self.configure(bg=theme["bg"])
        # The matplotlib figure background is handled when drawing.

    def on_theme_change(self, theme_dict):
        """Called when the application theme changes."""
        self._apply_theme_colors()
        self._refresh_graph()  # redraw with new colours