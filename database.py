"""SQLite persistence layer for the BMI Calculator.

Provides multi-user storage and historical records tracking with
robust error handling for database read/write operations.
"""

import os
import sqlite3
import csv
from datetime import datetime
from typing import List, Dict, Optional, Any


class DatabaseError(Exception):
    """Custom exception raised when a database operation fails."""
    pass


class BMIDatabase:
    """Manages SQLite storage for BMI users and records."""

    def __init__(self, db_path: Optional[str] = None):
        """Initializes the database connection.

        Args:
            db_path: Path to the SQLite .db file. If None, defaults to 'bmi_tracker.db'
                     in the same directory as this file.
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "bmi_tracker.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a SQLite connection with row factory enabled."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database at {self.db_path}: {e}") from e

    def _init_db(self) -> None:
        """Creates the necessary tables if they don't already exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
                """)
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Database initialization failed: {e}") from e

    # User Management
    def add_user(self, name: str) -> int:
        """Adds a new user to the database.

        Args:
            name: Non-empty user display name.

        Returns:
            The newly created user ID.

        Raises:
            DatabaseError: If name is invalid, user already exists, or DB write fails.
        """
        clean_name = name.strip()
        if not clean_name:
            raise DatabaseError("User name cannot be empty.")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name, created_at) VALUES (?, ?);",
                               (clean_name, datetime.now().isoformat()))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise DatabaseError(f"User '{clean_name}' already exists. Please choose another name.")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create user '{clean_name}': {e}") from e

    def get_users(self) -> List[Dict[str, Any]]:
        """Retrieves all users sorted by name.

        Returns:
            List of dicts with 'id', 'name', 'created_at'.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, created_at FROM users ORDER BY name ASC;")
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch users: {e}") from e

    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Finds user by name."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, created_at FROM users WHERE name = ?;", (name.strip(),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to find user '{name}': {e}") from e

    def get_or_create_default_user(self, default_name: str = "Default User") -> int:
        """Ensures at least one user exists and returns its ID."""
        user = self.get_user_by_name(default_name)
        if user:
            return user["id"]
        return self.add_user(default_name)

    # Records Management
    def add_record(self, user_id: int, weight: float, height: float, bmi: float,
                   category: str, timestamp: Optional[str] = None) -> int:
        """Adds a new BMI record for a user.

        Args:
            user_id: ID of the user.
            weight: Weight in kg.
            height: Height in meters.
            bmi: Calculated BMI.
            category: Classification category string.
            timestamp: ISO string or None (defaults to now).

        Returns:
            The inserted record ID.
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO records (user_id, weight, height, bmi, category, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (user_id, weight, height, bmi, category, timestamp))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to save BMI record: {e}") from e

    def get_records_for_user(self, user_id: int, order_desc: bool = False) -> List[Dict[str, Any]]:
        """Retrieves all BMI records for a given user.

        Args:
            user_id: The user ID.
            order_desc: If True, latest records appear first (useful for tables).
                        If False, chronological order (useful for charts).

        Returns:
            List of record dicts.
        """
        order_dir = "DESC" if order_desc else "ASC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT id, user_id, weight, height, bmi, category, timestamp
                    FROM records
                    WHERE user_id = ?
                    ORDER BY datetime(timestamp) {order_dir}, id {order_dir};
                """, (user_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch records for user ID {user_id}: {e}") from e

    def delete_record(self, record_id: int) -> bool:
        """Deletes a record by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM records WHERE id = ?;", (record_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete record ID {record_id}: {e}") from e

    def delete_user(self, user_id: int) -> bool:
        """Deletes a user and their cascading records."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete user ID {user_id}: {e}") from e

    def export_records_to_csv(self, user_id: int, filepath: str) -> int:
        """Exports all records for a user to a CSV file.

        Args:
            user_id: ID of the user.
            filepath: Destination CSV file path.

        Returns:
            Count of exported rows.
        """
        records = self.get_records_for_user(user_id, order_desc=False)
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Timestamp", "Weight (kg)", "Height (m)", "BMI", "Category"])
                for r in records:
                    writer.writerow([r["id"], r["timestamp"], r["weight"], r["height"], r["bmi"], r["category"]])
            return len(records)
        except OSError as e:
            raise DatabaseError(f"Failed to export CSV file to {filepath}: {e}") from e
