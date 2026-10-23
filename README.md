# Body Mass Index (BMI) Health Tracker

A Python application designed to calculate Body Mass Index (BMI) and classify it into standard health categories. This repository includes both a **Beginner Tier** interactive command-line tool and an **Advanced Tier** graphical user interface (GUI) desktop application featuring multi-user profiles, SQLite persistence, and Matplotlib trend visualization.

---

## Feature Checklist

### Beginner Tier
- [x] **CLI Prompts**: Prompts user for weight (kg) and height (m) via command line
- [x] **BMI Formula**: Calculates BMI using $\text{BMI} = \frac{\text{weight}}{\text{height}^2}$
- [x] **WHO Classification**:
  - Underweight: $< 18.5$
  - Normal: $18.5 – 24.9$
  - Overweight: $25.0 – 29.9$
  - Obese: $\ge 30.0$
- [x] **Rounded Output**: Displays the BMI value rounded to 2 decimal places with its category and health guidance
- [x] **Input Validation**: Rejects non-numeric, zero, negative, and extreme values with helpful error messages

### Advanced Tier
- [x] **GUI Window**: Modern desktop GUI built using `tkinter` and `ttk`
- [x] **Input Fields**: Labeled entries for weight and height with unit toggle (meters/cm) and "Calculate & Save" action
- [x] **Color-Coded Feedback**: Dynamic badge indicating health category (Green = Normal, Red = Obese, Amber = Overweight, Blue = Underweight)
- [x] **Multi-User Support**: Allows saving, switching, and creating independent profiles for named users
- [x] **Historical Records**: Stored in a local SQLite database (`bmi_tracker.db`) with an interactive Treeview table and CSV export option
- [x] **Graph View**: Interactive Matplotlib line chart tracking BMI progression over time with colored WHO reference zones
- [x] **Error Handling**: Comprehensive error handling for database read/write failures and input validation

---

## Project Structure

```
bmi_calculator/
├── bmi_core.py        # Core calculation, classification, and validation functions
├── bmi_cli.py         # Beginner Tier interactive command-line application
├── database.py        # SQLite persistence layer and CRUD operations
├── gui.py             # Advanced Tier Tkinter GUI with Matplotlib chart
├── main.py            # Unified application entry point
├── requirements.txt   # Project dependencies (matplotlib)
└── test_bmi.py        # Comprehensive unit & integration test suite (17 tests)
```

---

## Installation & Setup

1. **Prerequisites**: Python 3.8+
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Applications

### 1. Advanced GUI Application (Default)
To launch the full graphical interface:
```bash
python main.py
```
*(Or directly: `python gui.py`)*

#### GUI Features:
- **User Profile**: Select an existing user or click **+ New User** to create a new profile.
- **Calculate & Save**: Enter weight and height. The app computes the BMI, color-codes the result, saves the record to SQLite, and updates both the trend chart and the history table.
- **Trend Chart**: View your BMI over time against color-coded WHO health bands.
- **Historical Records**: Browse records, delete entries, or click **Export to CSV...** to export your data.

---

### 2. Beginner CLI Application
To launch the command-line tool:
```bash
python main.py --cli
```
*(Or directly: `python bmi_cli.py`)*

#### CLI Example:
```
=======================================================
           BODY MASS INDEX (BMI) CALCULATOR
=======================================================
Please enter your measurements below:

Enter your weight in kilograms (kg) [e.g., 70.0]: 70
Enter your height in meters (m)     [e.g., 1.75]: 1.75

-------------------------------------------------------
                     RESULTS
-------------------------------------------------------
 Weight entered  : 70.00 kg
 Height entered  : 1.75 m
 Calculated BMI  : 22.86
 Health Category : NORMAL
-------------------------------------------------------
 Guidance        : Your BMI falls within the healthy weight range. Keep up the good lifestyle and nutrition!
 Healthy Range   : For your height (1.75 m), the normal weight
                   range is between 56.7 kg and 76.3 kg.
=======================================================

Would you like to calculate another BMI? (y/n): n
Thank you for using the BMI Calculator. Stay healthy!
```

---

## Running Automated Tests

Run the full test suite with:
```bash
python -m unittest test_bmi.py -v
```
All 17 tests cover arithmetic calculations, boundary categories, input validation, and database CRUD/isolation operations.
