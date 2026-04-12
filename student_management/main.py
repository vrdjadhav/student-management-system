"""
Student Management System – Main Entry Point
---------------------------------------------
Initialises the application, database, theme manager,
and launches the main Tkinter window.
"""

import tkinter as tk
import sys
import os

# Ensure the project root is in the module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_TITLE, WINDOW_SIZE, DATABASE_NAME
from database.db_manager import DatabaseManager
from utils.theme_manager import ThemeManager
from views.main_window import MainWindow


def setup_database():
    """
    Create the database file (if not exists) and initialise the schema.
    Returns a DatabaseManager instance.
    """
    db_path = os.path.join(os.path.dirname(__file__), DATABASE_NAME)
    if not os.path.exists(db_path):
        print(f"[INFO] Creating new database at {db_path}")

    db = DatabaseManager()
    db.initialize_schema()
    return db


def main():
    """Application entry point."""
    # 1. Set up database
    db_manager = setup_database()

    # 2. Create the root Tk window
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_SIZE)
    root.minsize(1000, 600)

    # Center the window on the screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
    root.geometry(f"+{x}+{y}")

    # 3. Apply the default (light) theme
    ThemeManager.apply_theme("light", root)

    # 4. Create and pack the main application frame
    app = MainWindow(root, db_manager)
    app.pack(fill="both", expand=True)

    # 5. Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()