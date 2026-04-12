"""
Input Validators
----------------
Functions to validate common input fields such as email, phone number, and date.
"""

import re
from datetime import datetime


def validate_email(email: str) -> bool:
    """
    Validate an email address format.

    Args:
        email: The email string to validate.

    Returns:
        True if the email appears valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


def validate_phone(phone: str) -> bool:
    """
    Validate a phone number.
    Accepts 10-digit numbers, optionally with country code +91 or 0 prefix.
    Strips spaces and hyphens.

    Args:
        phone: The phone string to validate.

    Returns:
        True if the phone number is valid, False otherwise.
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone.strip())

    # Patterns:
    # - 10 digits (e.g., 9876543210)
    # - +91 followed by 10 digits
    # - 0 followed by 10 digits
    patterns = [
        r'^\d{10}$',
        r'^\+91\d{10}$',
        r'^0\d{10}$'
    ]

    return any(re.match(p, cleaned) for p in patterns)


def validate_date(date_str: str, date_format: str = "%d/%m/%Y") -> bool:
    """
    Validate a date string against a specified format.

    Args:
        date_str: The date string to validate.
        date_format: Expected format (default DD/MM/YYYY).

    Returns:
        True if the date is valid and matches the format, False otherwise.
    """
    if not date_str or not isinstance(date_str, str):
        return False

    # Additional check: ensure the string length is reasonable
    if len(date_str.strip()) < 6:
        return False

    try:
        datetime.strptime(date_str.strip(), date_format)
        return True
    except ValueError:
        return False


def validate_roll_number(roll: str) -> bool:
    """
    Validate a roll number.
    Allows alphanumeric characters, hyphens, and underscores.
    Length between 3 and 20 characters.

    Args:
        roll: The roll number string.

    Returns:
        True if valid, False otherwise.
    """
    if not roll or not isinstance(roll, str):
        return False

    roll = roll.strip()
    if not (3 <= len(roll) <= 20):
        return False

    pattern = r'^[A-Za-z0-9\-_]+$'
    return re.match(pattern, roll) is not None


def validate_name(name: str) -> bool:
    """
    Validate a person's full name.
    Allows letters, spaces, hyphens, and apostrophes.
    Length between 2 and 100 characters.

    Args:
        name: The name string.

    Returns:
        True if valid, False otherwise.
    """
    if not name or not isinstance(name, str):
        return False

    name = name.strip()
    if not (2 <= len(name) <= 100):
        return False

    # Allow letters (including accented), spaces, hyphens, apostrophes
    pattern = r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$"
    return re.match(pattern, name) is not None


def validate_address(address: str) -> bool:
    """
    Validate an address.
    Requires at least 5 characters.

    Args:
        address: The address string.

    Returns:
        True if valid, False otherwise.
    """
    if not address or not isinstance(address, str):
        return False
    return len(address.strip()) >= 5