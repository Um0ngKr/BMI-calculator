"""Advanced Tier: Full Graphical User Interface (GUI) for BMI Calculator.

Built with Tkinter, SQLite3, and Matplotlib.
Features:
  - Multi-user profiles with dropdown selector and user creation modal
  - Input fields with labels for Weight (kg) and Height (m/cm)
  - Color-coded visual feedback badge (Green: Normal, Red: Obese, Amber: Overweight, Blue: Underweight)
  - Historical records table with delete and CSV export capability
  - Interactive Matplotlib trend chart embedded in GUI with WHO health threshold zones
  - Comprehensive error handling for input validation and database operations
"""

import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Matplotlib embedded in Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates

try:
    from bmi_core import (
        calculate_bmi,
        classify_bmi,
        validate_measurements,
        get_ideal_weight_range,
        ValidationError
    )
    from database import BMIDatabase, DatabaseError
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from bmi_core import (
        calculate_bmi,
        classify_bmi,
        validate_measurements,
        get_ideal_weight_range,
        ValidationError
    )
    from database import BMIDatabase, DatabaseError


class BMIGUIApp(tk.Tk):
    """Main GUI Application window for BMI calculation and tracking."""

    def __init__(self):
        super().__init__()
        self.title("Body Mass Index (BMI) Health Tracker")
        self.geometry("1060x760")
        self.minsize(920, 680)

        # Database initialization with error catching
        try:
            self.db = BMIDatabase()
            self.current_user_id = self.db.get_or_create_default_user("Default User")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{e}")
            self.destroy()
            return

        self.users_cache = []
        self._configure_styles()
        self._build_ui()
        self._load_users()
        self._refresh_data()

    def _configure_styles(self):
        """Sets up ttk styles with a clean modern palette."""
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Colors
        self.bg_color = "#f4f6f9"
        self.card_bg = "#ffffff"
        self.accent_color = "#1976d2"
        self.text_dark = "#212529"
        self.configure(bg=self.bg_color)

        self.style.configure(".", background=self.bg_color, foreground=self.text_dark, font=("Segoe UI", 10))
        self.style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0d47a1", background=self.bg_color)
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#616161", background=self.bg_color)
        self.style.configure("CardTitle.TLabel", font=("Segoe UI", 12, "bold"), foreground="#263238", background=self.card_bg)
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))

    def _build_ui(self):
        """Constructs the application layout."""
        # Top Header Banner
        header_frame = ttk.Frame(self, padding=(20, 15, 20, 10))
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="Body Mass Index (BMI) Health Tracker", style="Header.TLabel")
        title_lbl.pack(anchor="w")
        subtitle_lbl = ttk.Label(header_frame, text="Calculate, track, and visualize your body mass index progression over time.", style="SubHeader.TLabel")
        subtitle_lbl.pack(anchor="w")

        # Main Split Content (Left: Inputs & Results, Right: Visuals & History)
        main_container = ttk.Frame(self, padding=(15, 5, 15, 15))
        main_container.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_container, width=380)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Build individual sections
        self._build_user_card(left_panel)
        self._build_input_card(left_panel)
        self._build_result_card(left_panel)
        self._build_tabs(right_panel)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w",
                               padding=(10, 4), font=("Segoe UI", 9), foreground="#555555")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_user_card(self, parent):
        """Builds user profile selection card."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(card, text="Active User Profile", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill=tk.X)

        self.user_combo = ttk.Combobox(row, state="readonly", font=("Segoe UI", 10))
        self.user_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.user_combo.bind("<<ComboboxSelected>>", self._on_user_changed)

        new_user_btn = ttk.Button(row, text="+ New User", command=self._add_new_user)
        new_user_btn.pack(side=tk.RIGHT)

    def _build_input_card(self, parent):
        """Builds weight & height input card."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(card, text="Enter Measurements", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))

        # Weight row
        ttk.Label(card, text="Weight (kg):", background=self.card_bg, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.weight_var = tk.StringVar()
        self.weight_entry = ttk.Entry(card, textvariable=self.weight_var, font=("Segoe UI", 11))
        self.weight_entry.pack(fill=tk.X, pady=(2, 10))

        # Height row with unit helper
        h_label_frame = ttk.Frame(card, style="Card.TFrame")
        h_label_frame.pack(fill=tk.X)
        ttk.Label(h_label_frame, text="Height:", background=self.card_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        self.height_unit_var = tk.StringVar(value="meters")
        unit_meter = ttk.Radiobutton(h_label_frame, text="Meters (m)", variable=self.height_unit_var,
                                     value="meters", style="Card.TRadiobutton", command=self._on_unit_change)
        unit_meter.pack(side=tk.RIGHT)
        unit_cm = ttk.Radiobutton(h_label_frame, text="cm", variable=self.height_unit_var,
                                  value="cm", style="Card.TRadiobutton", command=self._on_unit_change)
        unit_cm.pack(side=tk.RIGHT, padx=4)

        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(card, textvariable=self.height_var, font=("Segoe UI", 11))
        self.height_entry.pack(fill=tk.X, pady=(2, 12))

        # Buttons
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        self.calc_btn = ttk.Button(btn_frame, text="Calculate & Save", style="Action.TButton", command=self._calculate_and_save)
        self.calc_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        clear_btn = ttk.Button(btn_frame, text="Clear", command=self._clear_inputs)
        clear_btn.pack(side=tk.RIGHT)

    def _build_result_card(self, parent):
        """Builds result feedback badge card."""
        self.result_card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        self.result_card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.result_card, text="BMI Assessment", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        # Value display
        self.bmi_display_lbl = tk.Label(
            self.result_card,
            text="--.--",
            font=("Segoe UI", 32, "bold"),
            bg="#eceff1",
            fg="#455a64",
            pady=8,
            relief="groove"
        )
        self.bmi_display_lbl.pack(fill=tk.X, pady=(0, 8))

        # Category Badge
        self.badge_lbl = tk.Label(
            self.result_card,
            text="Awaiting calculation",
            font=("Segoe UI", 12, "bold"),
            bg="#90a4ae",
            fg="#ffffff",
            pady=4,
            relief="flat"
        )
        self.badge_lbl.pack(fill=tk.X, pady=(0, 8))

        # Description text
        self.desc_lbl = tk.Label(
            self.result_card,
            text="Enter weight and height, then click 'Calculate & Save' to record your BMI.",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg="#555555",
            wraplength=320,
            justify=tk.LEFT
        )
        self.desc_lbl.pack(anchor="w", pady=(0, 6))

        # Healthy range guideline
        self.healthy_range_lbl = tk.Label(
            self.result_card,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=self.card_bg,
            fg="#2e7d32",
            wraplength=320,
            justify=tk.LEFT
        )
        self.healthy_range_lbl.pack(anchor="w")

    def _build_tabs(self, parent):
        """Builds right panel tabs: Trend Chart and History Table."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Matplotlib Chart
        chart_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(chart_tab, text="  BMI Trend Chart  ")

        self.fig = Figure(figsize=(6, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_tab)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, chart_tab)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Tab 2: History Table
        history_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(history_tab, text="  Historical Records  ")

        cols = ("id", "date", "weight", "height", "bmi", "category")
        self.tree = ttk.Treeview(history_tab, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date & Time")
        self.tree.heading("weight", text="Weight (kg)")
        self.tree.heading("height", text="Height (m)")
        self.tree.heading("bmi", text="BMI")
        self.tree.heading("category", text="Category")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("date", width=150, anchor="center")
        self.tree.column("weight", width=95, anchor="center")
        self.tree.column("height", width=95, anchor="center")
        self.tree.column("bmi", width=85, anchor="center")
        self.tree.column("category", width=120, anchor="center")

        tree_scroll = ttk.Scrollbar(history_tab, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Table Action Buttons
        tbl_btn_frame = ttk.Frame(history_tab, padding=(0, 10, 0, 0))
        tbl_btn_frame.pack(fill=tk.X)

        del_btn = ttk.Button(tbl_btn_frame, text="Delete Selected Record", command=self._delete_selected_record)
        del_btn.pack(side=tk.LEFT, padx=(0, 6))

        export_btn = ttk.Button(tbl_btn_frame, text="Export to CSV...", command=self._export_csv)
        export_btn.pack(side=tk.LEFT)

    def _on_unit_change(self):
        """Helps convert height input if unit radio changes."""
        val = self.height_var.get().strip()
        if not val:
            return
        try:
            h = float(val)
            if self.height_unit_var.get() == "cm" and h < 3.0:
                self.height_var.set(f"{h * 100:.1f}")
            elif self.height_unit_var.get() == "meters" and h > 10.0:
                self.height_var.set(f"{h / 100:.2f}")
        except ValueError:
            pass

    def _load_users(self):
        """Loads users into dropdown."""
        try:
            self.users_cache = self.db.get_users()
            user_names = [u["name"] for u in self.users_cache]
            self.user_combo["values"] = user_names

            # Select current user
            for u in self.users_cache:
                if u["id"] == self.current_user_id:
                    self.user_combo.set(u["name"])
                    break
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to load user list:\n{e}")

    def _add_new_user(self):
        """Opens prompt to create a new user."""
        name = simpledialog.askstring("Add New User", "Enter new user profile name:", parent=self)
        if not name:
            return
        try:
            new_id = self.db.add_user(name)
            self.current_user_id = new_id
            self._load_users()
            self._refresh_data()
            self.status_var.set(f"Created and switched to user '{name}'.")
        except DatabaseError as e:
            messagebox.showerror("Error Adding User", str(e))

    def _on_user_changed(self, event=None):
        """Handles user switching."""
        selected_name = self.user_combo.get()
        for u in self.users_cache:
            if u["name"] == selected_name:
                self.current_user_id = u["id"]
                break
        self._refresh_data()
        self.status_var.set(f"Switched profile to '{selected_name}'.")

    def _clear_inputs(self):
        """Clears measurement input fields."""
        self.weight_var.set("")
        self.height_var.set("")
        self.bmi_display_lbl.config(text="--.--", bg="#eceff1", fg="#455a64")
        self.badge_lbl.config(text="Awaiting calculation", bg="#90a4ae", fg="#ffffff")
        self.desc_lbl.config(text="Enter weight and height, then click 'Calculate & Save'.")
        self.healthy_range_lbl.config(text="")
        self.status_var.set("Inputs cleared.")

    def _calculate_and_save(self):
        """Validates inputs, computes BMI, saves to DB, and updates visuals."""
        weight_str = self.weight_var.get().strip()
        height_str = self.height_var.get().strip()

        # Handle height unit conversion if in cm
        if self.height_unit_var.get() == "cm":
            try:
                cm_val = float(height_str)
                height_str = str(cm_val / 100.0)
            except ValueError:
                pass

        try:
            weight_kg, height_m = validate_measurements(weight_str, height_str)
        except ValidationError as e:
            messagebox.showwarning("Invalid Input", str(e))
            return

        bmi = calculate_bmi(weight_kg, height_m)
        info = classify_bmi(bmi)
        ideal_min, ideal_max = get_ideal_weight_range(height_m)

        # Update Result Card
        self.bmi_display_lbl.config(
            text=f"{bmi:.2f}",
            bg=info["color"],
            fg=info["text_color"]
        )
        self.badge_lbl.config(
            text=info["category"].upper(),
            bg=info["color"],
            fg=info["text_color"]
        )
        self.desc_lbl.config(text=info["description"])
        self.healthy_range_lbl.config(
            text=f"Normal weight for {height_m:.2f} m: {ideal_min:.1f} kg – {ideal_max:.1f} kg"
        )

        # Save to SQLite Database
        try:
            self.db.add_record(
                user_id=self.current_user_id,
                weight=weight_kg,
                height=height_m,
                bmi=bmi,
                category=info["category"]
            )
            self._refresh_data()
            self.status_var.set(f"Saved: BMI {bmi:.2f} ({info['category']}) recorded successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to save record to database:\n{e}")

    def _refresh_data(self):
        """Refreshes both the history table and the trend chart."""
        try:
            records = self.db.get_records_for_user(self.current_user_id, order_desc=True)
            self._update_table(records)
            self._update_chart()
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to refresh data:\n{e}")

    def _update_table(self, records):
        """Populates the treeview table with records."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in records:
            self.tree.insert("", tk.END, values=(
                r["id"],
                r["timestamp"],
                f"{r['weight']:.2f}",
                f"{r['height']:.2f}",
                f"{r['bmi']:.2f}",
                r["category"]
            ))

    def _update_chart(self):
        """Redraws the Matplotlib trend line chart."""
        self.ax.clear()

        # Get records in chronological order
        records = self.db.get_records_for_user(self.current_user_id, order_desc=False)

        if not records:
            self.ax.text(
                0.5, 0.5,
                "No BMI records found for this user.\nCalculate and save measurements to see the trend!",
                horizontalalignment="center",
                verticalalignment="center",
                transform=self.ax.transAxes,
                fontsize=11,
                color="#78909c"
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
            return

        dates = []
        bmis = []
        for r in records:
            try:
                dt = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.fromisoformat(r["timestamp"])
                except Exception:
                    dt = datetime.now()
            dates.append(dt)
            bmis.append(r["bmi"])

        # Determine y-limits with headroom for bands
        min_y = min(min(bmis) - 2, 16.0)
        max_y = max(max(bmis) + 3, 35.0)

        # Color reference zones for WHO standards
        self.ax.axhspan(min_y, 18.5, color="#0288D1", alpha=0.10, label="Underweight (<18.5)")
        self.ax.axhspan(18.5, 24.9, color="#2E7D32", alpha=0.15, label="Normal (18.5–24.9)")
        self.ax.axhspan(24.9, 29.9, color="#F57F17", alpha=0.12, label="Overweight (25–29.9)")
        self.ax.axhspan(29.9, max_y, color="#D32F2F", alpha=0.12, label="Obese (≥30)")

        # Threshold guide lines
        self.ax.axhline(18.5, color="#0288D1", linestyle="--", linewidth=0.9)
        self.ax.axhline(24.9, color="#2E7D32", linestyle="--", linewidth=0.9)
        self.ax.axhline(29.9, color="#D32F2F", linestyle="--", linewidth=0.9)

        # Plot Trend Line
        self.ax.plot(
            dates,
            bmis,
            marker="o",
            color="#1565C0",
            linewidth=2.2,
            markersize=6,
            label="User BMI"
        )

        # Annotate points with their values
        for d, b in zip(dates, bmis):
            self.ax.annotate(
                f"{b:.1f}",
                (d, b),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
                fontweight="bold",
                color="#0d47a1"
            )

        self.ax.set_ylim(min_y, max_y)
        self.ax.set_ylabel("BMI Value", fontsize=10, fontweight="bold")
        self.ax.set_title("BMI Trend Over Time", fontsize=12, fontweight="bold", pad=10)
        self.ax.grid(True, linestyle=":", alpha=0.6)

        # Format X-axis Dates
        if len(dates) > 1:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M"))
            self.fig.autofmt_xdate(rotation=0, ha="center")
        else:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))

        self.ax.legend(loc="upper left", fontsize=8, framealpha=0.85)
        self.fig.tight_layout()
        self.canvas.draw()

    def _delete_selected_record(self):
        """Deletes selected item in history treeview."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please select a record from the table to delete.")
            return

        item = self.tree.item(selected[0])
        rec_id = item["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete record ID #{rec_id}?",
            parent=self
        )
        if not confirm:
            return

        try:
            self.db.delete_record(rec_id)
            self._refresh_data()
            self.status_var.set(f"Record #{rec_id} deleted successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to delete record:\n{e}")

    def _export_csv(self):
        """Exports user records to a CSV file."""
        records = self.db.get_records_for_user(self.current_user_id)
        if not records:
            messagebox.showinfo("Export CSV", "No records available to export for this user.")
            return

        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Save Records as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files (*.csv)", "*.csv"), ("All files (*.*)", "*.*")],
            initialfile=f"bmi_records_user_{self.current_user_id}.csv"
        )
        if not filepath:
            return

        try:
            count = self.db.export_records_to_csv(self.current_user_id, filepath)
            messagebox.showinfo("Export Successful", f"Successfully exported {count} records to:\n{filepath}")
            self.status_var.set(f"Exported {count} records to {os.path.basename(filepath)}.")
        except DatabaseError as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")


def launch_gui():
    """Starts the Tkinter application."""
    app = BMIGUIApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
