"""Beginner Tier: Command-Line BMI Calculator.

Features:
  - Interactive CLI prompts for weight (kg) and height (m)
  - Formula: BMI = weight / (height ^ 2)
  - WHO Classification categories (Underweight, Normal, Overweight, Obese)
  - Display rounded to 2 decimal places with category and feedback
  - Input validation: Rejects non-numeric, negative, and zero values with clear explanations
  - Repeat prompt loop to calculate multiple times
"""

import sys
try:
    from bmi_core import calculate_bmi, classify_bmi, validate_measurements, get_ideal_weight_range, ValidationError
except ImportError:
    # If run in a path where bmi_core isn't directly resolved
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from bmi_core import calculate_bmi, classify_bmi, validate_measurements, get_ideal_weight_range, ValidationError


def prompt_positive_float(prompt_message: str, measurement_name: str, unit: str) -> float:
    """Prompts the user for a numeric value until a valid positive float is provided."""
    while True:
        user_input = input(prompt_message).strip()
        if not user_input:
            print(f" Error: {measurement_name} cannot be empty. Please enter a number in {unit}.")
            continue
        try:
            value = float(user_input)
        except ValueError:
            print(f" Error: '{user_input}' is not a valid number. Please enter numeric digits (e.g., 68.5).")
            continue

        if value <= 0:
            print(f" Error: {measurement_name} must be strictly positive (greater than 0 {unit}). You entered: {value}")
            continue

        return value


def run_bmi_calculator():
    """Runs a single round of BMI calculation via CLI."""
    print("\n" + "=" * 55)
    print("           BODY MASS INDEX (BMI) CALCULATOR")
    print("=" * 55)
    print("Please enter your measurements below:")

    # Step 1: Prompt and validate weight
    while True:
        weight_input = input("\nEnter your weight in kilograms (kg) [e.g., 70.0]: ").strip()
        try:
            from bmi_core import validate_weight
            weight_kg = validate_weight(weight_input)
            break
        except ValidationError as err:
            print(f"  Input Error: {err}")

    # Step 2: Prompt and validate height
    while True:
        height_input = input("Enter your height in meters (m)     [e.g., 1.75]: ").strip()
        try:
            from bmi_core import validate_height
            height_m = validate_height(height_input)
            break
        except ValidationError as err:
            print(f"  Input Error: {err}")

    # Calculate BMI
    bmi = calculate_bmi(weight_kg, height_m)
    info = classify_bmi(bmi)
    ideal_min, ideal_max = get_ideal_weight_range(height_m)

    # Display results
    print("\n" + "-" * 55)
    print("                     RESULTS")
    print("-" * 55)
    print(f" Weight entered  : {weight_kg:.2f} kg")
    print(f" Height entered  : {height_m:.2f} m")
    print(f" Calculated BMI  : {bmi:.2f}")
    print(f" Health Category : {info['category'].upper()}")
    print("-" * 55)
    print(f" Guidance        : {info['description']}")
    print(f" Healthy Range   : For your height ({height_m:.2f} m), the normal weight")
    print(f"                   range is between {ideal_min:.1f} kg and {ideal_max:.1f} kg.")
    print("=" * 55)


def main():
    """Main CLI entrypoint with replay option."""
    print("=" * 55)
    print(" Welcome to the Python BMI & Health Category Calculator!")
    print("=" * 55)

    while True:
        run_bmi_calculator()
        choice = input("\nWould you like to calculate another BMI? (y/n): ").strip().lower()
        if choice not in ("y", "yes"):
            print("\nThank you for using the BMI Calculator. Stay healthy!\n")
            break


if __name__ == "__main__":
    main()
