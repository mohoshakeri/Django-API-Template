#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This module provides the main entry point for Django management commands.
"""

import os
import sys


def main() -> None:
    """
    Run administrative tasks.

    Sets up the Django environment and executes management commands from the command line.

    Raises:
        ImportError: If Django is not properly installed or virtual environment is not activated
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_title.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
