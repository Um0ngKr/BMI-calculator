"""Entry point for Body Mass Index (BMI) Health Tracker.

Usage:
    python main.py          # Launches the Advanced GUI desktop application (default)
    python main.py --cli    # Runs the Beginner Tier interactive CLI tool
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Body Mass Index (BMI) Calculator & Health Tracker"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch the Beginner Tier interactive Command-Line Interface instead of the GUI."
    )
    args = parser.parse_args()

    if args.cli:
        from bmi_cli import main as cli_main
        cli_main()
    else:
        try:
            from gui import launch_gui
            launch_gui()
        except ImportError as e:
            print(f"[Warning] GUI dependencies failed to load: {e}")
            print("Falling back to Command-Line Interface mode...\n")
            from bmi_cli import main as cli_main
            cli_main()


if __name__ == "__main__":
    main()
