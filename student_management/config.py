"""
Application Constants and Configuration
---------------------------------------
Contains theme colours, window settings, database name,
and column definitions for the student table.
"""

# ─────────────────────────────────────────────────────────────
#  APPLICATION METADATA
# ─────────────────────────────────────────────────────────────
APP_TITLE = "Student Management System"
WINDOW_SIZE = "1200x700"
DATABASE_NAME = "students.db"

# ─────────────────────────────────────────────────────────────
#  STUDENT TABLE COLUMNS (used for Treeview headings)
# ─────────────────────────────────────────────────────────────
STUDENT_COLUMNS = (
    "Roll_No",
    "Name",
    "Email",
    "Gender",
    "Contact",
    "DOB",
    "Address"
)

STUDENT_COLUMN_WIDTHS = (80, 130, 170, 70, 110, 90, 160)

# Field labels for the form (mapping internal key to display text)
STUDENT_FORM_FIELDS = [
    ("Roll No *",      "roll_no",  "entry", None),
    ("Full Name *",    "name",     "entry", None),
    ("Email *",        "email",    "entry", None),
    ("Gender *",       "gender",   "combo", ["Male", "Female", "Other"]),
    ("Contact *",      "contact",  "entry", None),
    ("Date of Birth *","dob",      "entry", None),
    ("Address *",      "address",  "text",  None),
]

# ─────────────────────────────────────────────────────────────
#  THEME COLOUR PALETTES
# ─────────────────────────────────────────────────────────────
class Themes:
    """Colour definitions for light and dark modes."""

    LIGHT = {
        # General
        "bg":          "#F0F2F5",   # window background
        "panel":       "#FFFFFF",   # card panels
        "border":      "#E0E0E0",   # subtle borders
        "text":        "#37474F",   # primary text colour
        "label":       "#37474F",   # form labels
        "entry_bg":    "#FAFAFA",   # entry/combobox background

        # Header
        "header":      "#1A237E",   # deep indigo
        "header_text": "#FFFFFF",

        # Accent
        "accent":      "#3949AB",   # indigo accent

        # Buttons
        "add_btn":     "#2E7D32",   # green
        "add_hover":   "#1B5E20",
        "upd_btn":     "#1565C0",   # blue
        "upd_hover":   "#0D47A1",
        "del_btn":     "#C62828",   # red
        "del_hover":   "#7F0000",
        "clr_btn":     "#546E7A",   # slate
        "clr_hover":   "#263238",

        # Treeview
        "tree_bg":     "#FFFFFF",
        "tree_fg":     "#37474F",
        "tree_field":  "#FFFFFF",
        "tree_select": "#C5CAE9",
        "tree_header": "#3949AB",
        "row_odd":     "#F5F5F5",
        "row_even":    "#FFFFFF",
    }

    DARK = {
        # General
        "bg":          "#121212",
        "panel":       "#1E1E1E",
        "border":      "#333333",
        "text":        "#E0E0E0",
        "label":       "#B0BEC5",
        "entry_bg":    "#2D2D2D",

        # Header
        "header":      "#0D1B2A",
        "header_text": "#E0E0E0",

        # Accent
        "accent":      "#415A77",

        # Buttons
        "add_btn":     "#1B5E20",
        "add_hover":   "#2E7D32",
        "upd_btn":     "#0D47A1",
        "upd_hover":   "#1565C0",
        "del_btn":     "#7F0000",
        "del_hover":   "#C62828",
        "clr_btn":     "#37474F",
        "clr_hover":   "#546E7A",

        # Treeview
        "tree_bg":     "#1E1E1E",
        "tree_fg":     "#E0E0E0",
        "tree_field":  "#1E1E1E",
        "tree_select": "#415A77",
        "tree_header": "#1A2A3A",
        "row_odd":     "#2A2A2A",
        "row_even":    "#1E1E1E",
    }