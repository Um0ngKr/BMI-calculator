"""Core BMI calculation, classification, and validation module.

Formula: BMI = weight (kg) / (height (m))^2
Standard Categories (WHO):
  - Underweight: < 18.5
  - Normal:      18.5 - 24.9
  - Overweight:  25.0 - 29.9
  - Obese:       >= 30.0
"""

from typing import Dict, Tuple, Any


class ValidationError(ValueError):
    """Raised when user input for weight or height is invalid."""
    pass


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculates BMI given weight in kilograms and height in meters.

    Args:
        weight_kg: Weight in kilograms (> 0).
        height_m: Height in meters (> 0).

    Returns:
        BMI value rounded to 2 decimal places.

    Raises:
        ValidationError: If weight or height are non-positive.
    """
    if weight_kg <= 0:
        raise ValidationError("Weight must be greater than zero.")
    if height_m <= 0:
        raise ValidationError("Height must be greater than zero.")

    raw_bmi = weight_kg / (height_m ** 2)
    return round(raw_bmi, 2)


def classify_bmi(bmi: float) -> Dict[str, Any]:
    """Classifies a BMI value into standard health categories.

    Args:
        bmi: The Body Mass Index value.

    Returns:
        Dict with keys:
          - category: Standard category name ("Underweight", "Normal", "Overweight", "Obese")
          - color: Hex color code suitable for GUI badges
          - text_color: Contrasting text color
          - description: Health guidance summary
    """
    if bmi < 18.5:
        return {
            "category": "Underweight",
            "color": "#0288D1",  # Blue
            "text_color": "#FFFFFF",
            "description": "Your BMI indicates you may be underweight. A balanced, nutrient-dense diet is recommended."
        }
    elif bmi <= 24.9:
        return {
            "category": "Normal",
            "color": "#2E7D32",  # Green
            "text_color": "#FFFFFF",
            "description": "Your BMI falls within the healthy weight range. Keep up the good lifestyle and nutrition!"
        }
    elif bmi <= 29.9:
        return {
            "category": "Overweight",
            "color": "#F57F17",  # Amber/Orange
            "text_color": "#FFFFFF",
            "description": "Your BMI indicates you are in the overweight range. Regular activity and mindful eating may help."
        }
    else:
        return {
            "category": "Obese",
            "color": "#D32F2F",  # Red
            "text_color": "#FFFFFF",
            "description": "Your BMI indicates obesity. Consulting a healthcare provider for personalized guidance is recommended."
        }


def validate_weight(weight_str: str) -> float:
    """Validates raw string input for weight in kg."""
    if not weight_str or not weight_str.strip():
        raise ValidationError("Weight cannot be empty. Please enter a positive number in kg.")
    try:
        weight = float(weight_str.strip())
    except ValueError:
        raise ValidationError(f"Invalid weight '{weight_str}'. Please enter a valid number (e.g., 68.5).")
    if weight <= 0:
        raise ValidationError("Weight must be greater than 0 kg.")
    if weight < 10.0:
        raise ValidationError(f"Weight of {weight} kg is below minimum realistic human limit (10 kg).")
    if weight > 650.0:
        raise ValidationError(f"Weight of {weight} kg exceeds realistic limits (max 650 kg).")
    return weight


def validate_height(height_str: str) -> float:
    """Validates raw string input for height in meters."""
    if not height_str or not height_str.strip():
        raise ValidationError("Height cannot be empty. Please enter a positive number in meters.")
    try:
        height = float(height_str.strip())
    except ValueError:
        raise ValidationError(f"Invalid height '{height_str}'. Please enter a valid number (e.g., 1.75).")
    if height <= 0:
        raise ValidationError("Height must be greater than 0 meters.")
    if height > 3.0:
        if height <= 300.0:
            converted = height / 100.0
            raise ValidationError(
                f"Height of {height} appears to be in centimeters. "
                f"Please enter in meters (e.g., {converted:.2f} m)."
            )
        raise ValidationError(f"Height of {height} m is unrealistically large. Please check your value.")
    if height < 0.5:
        raise ValidationError(f"Height of {height} m is unrealistically small (minimum is 0.5 m).")
    return height


def validate_measurements(weight_str: str, height_str: str) -> Tuple[float, float]:
    """Validates raw string inputs for weight and height."""
    weight = validate_weight(weight_str)
    height = validate_height(height_str)
    return weight, height



def get_ideal_weight_range(height_m: float) -> Tuple[float, float]:
    """Calculates healthy weight range (BMI 18.5 to 24.9) for a given height in meters.

    Returns:
        Tuple of (min_weight_kg, max_weight_kg) rounded to 1 decimal place.
    """
    if height_m <= 0:
        return (0.0, 0.0)
    min_weight = round(18.5 * (height_m ** 2), 1)
    max_weight = round(24.9 * (height_m ** 2), 1)
    return (min_weight, max_weight)
