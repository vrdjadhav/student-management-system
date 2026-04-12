"""
Theme Manager Utility
---------------------
Handles light/dark theme toggling for the entire application.
Applies ttk styles and notifies all registered views when the theme changes.
"""

import tkinter as tk
from tkinter import ttk
from config import Themes


class ThemeManager:
    """
    Central theme controller with observer pattern.
    Views can register callbacks to update custom widget colours.
    """

    _current_theme = "light"
    _observers = []

    @classmethod
    def apply_theme(cls, theme_name: str, root: tk.Tk) -> None:
        """
        Apply the selected theme to the root window and all ttk widgets.

        Args:
            theme_name: Either "light" or "dark".
            root: The root Tk window instance.
        """
        if theme_name not in ("light", "dark"):
            raise ValueError("theme_name must be 'light' or 'dark'")

        theme = Themes.LIGHT if theme_name == "light" else Themes.DARK
        cls._current_theme = theme_name

        # Configure root window background
        root.configure(bg=theme["bg"])

        # Configure ttk styles
        style = ttk.Style()
        style.theme_use("clam")

        # --- Treeview ---
        style.configure(
            "Custom.Treeview",
            background=theme["tree_bg"],
            foreground=theme["tree_fg"],
            fieldbackground=theme["tree_field"],
            rowheight=28,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=theme["tree_header"],
            foreground="white",
            font=("Segoe UI Semibold", 10),
            relief="flat",
            padding=(5, 5)
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", theme["tree_select"])],
            foreground=[("selected", theme["header"])]
        )

        # --- Entry ---
        style.configure(
            "TEntry",
            fieldbackground=theme["entry_bg"],
            foreground=theme["text"],
            borderwidth=1,
            relief="solid"
        )

        # --- Combobox ---
        style.configure(
            "TCombobox",
            fieldbackground=theme["entry_bg"],
            foreground=theme["text"],
            arrowcolor=theme["text"]
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme["entry_bg"])],
            selectbackground=[("readonly", theme["accent"])],
            selectforeground=[("readonly", "white")]
        )

        # --- Button (ttk) ---
        style.configure(
            "TButton",
            background=theme["accent"],
            foreground="white",
            borderwidth=0,
            focusthickness=3,
            focuscolor="none",
            font=("Segoe UI", 10)
        )
        style.map(
            "TButton",
            background=[("active", theme["accent"]), ("pressed", theme["header"])],
            foreground=[("active", "white")]
        )

        # --- Label (ttk) ---
        style.configure(
            "TLabel",
            background=theme["panel"],
            foreground=theme["text"],
            font=("Segoe UI", 10)
        )

        # --- Frame (ttk) ---
        style.configure(
            "TFrame",
            background=theme["panel"]
        )

        # --- Labelframe ---
        style.configure(
            "TLabelframe",
            background=theme["panel"],
            foreground=theme["text"],
            bordercolor=theme["border"]
        )
        style.configure(
            "TLabelframe.Label",
            background=theme["panel"],
            foreground=theme["text"]
        )

        # --- Notebook (tabs) ---
        style.configure(
            "TNotebook",
            background=theme["panel"],
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=theme["panel"],
            foreground=theme["text"],
            padding=[10, 4],
            font=("Segoe UI", 10)
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", theme["accent"])],
            foreground=[("selected", "white")]
        )

        # --- Scrollbar ---
        style.configure(
            "TScrollbar",
            background=theme["panel"],
            troughcolor=theme["entry_bg"],
            arrowcolor=theme["text"]
        )

        # Notify all registered observers
        for observer in cls._observers:
            try:
                observer(theme)
            except Exception as e:
                print(f"[ThemeManager] Observer error: {e}")

    @classmethod
    def register_observer(cls, callback) -> None:
        """
        Register a callback to be called when the theme changes.
        The callback receives one argument: the new theme dictionary.
        """
        if callback not in cls._observers:
            cls._observers.append(callback)

    @classmethod
    def unregister_observer(cls, callback) -> None:
        """
        Remove a previously registered observer.
        """
        if callback in cls._observers:
            cls._observers.remove(callback)

    @classmethod
    def get_current_theme_name(cls) -> str:
        """Return the current theme name ('light' or 'dark')."""
        return cls._current_theme

    @classmethod
    def get_current_theme_dict(cls) -> dict:
        """Return the colour dictionary for the current theme."""
        return Themes.LIGHT if cls._current_theme == "light" else Themes.DARK

    @classmethod
    def toggle_theme(cls, root: tk.Tk) -> str:
        """
        Toggle between light and dark themes and apply.
        Returns the new theme name.
        """
        new_theme = "dark" if cls._current_theme == "light" else "light"
        cls.apply_theme(new_theme, root)
        return new_theme