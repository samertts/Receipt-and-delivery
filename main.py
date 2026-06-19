"""
نظام إدارة الاستلام المختبري
Iraqi Laboratory Receipt & Delivery Management System

Entry point for the desktop application (PySide6).
For the web API backend, run: uvicorn app.main:app --reload
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        from lab_system.app.ui.app import run

        run()
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
