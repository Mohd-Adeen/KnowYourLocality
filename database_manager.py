"""
Database Manager for KnowYourLocality
-------------------------------------
Handles SQLite persistence for:
1. Contact messages submitted via /contact.
2. Saved / bookmarked localities for quick citizen monitoring.
3. Citizen locality safety feedback and observations.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locality_civic.db')

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Contact form inquiries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contact_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Saved / Bookmarked localities
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL UNIQUE,
                    safety_score INTEGER,
                    crime_rate REAL,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Citizen community safety feedback
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS safety_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    category TEXT,
                    comment TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_contact_message(self, name, email, message):
        """Saves a message from the contact form."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)',
                (name.strip(), email.strip(), message.strip())
            )
            conn.commit()
            return cursor.lastrowid

    def get_contact_messages(self, limit=50):
        """Retrieves recent contact messages."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM contact_messages ORDER BY submitted_at DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def save_location(self, location, safety_score=None, crime_rate=None):
        """Saves or updates a bookmarked location."""
        loc_clean = location.strip().title()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO saved_locations (location, safety_score, crime_rate, saved_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(location) DO UPDATE SET
                    safety_score=excluded.safety_score,
                    crime_rate=excluded.crime_rate,
                    saved_at=CURRENT_TIMESTAMP
            ''', (loc_clean, safety_score, crime_rate))
            conn.commit()
            return True

    def remove_saved_location(self, location):
        """Removes a location from bookmarks."""
        loc_clean = location.strip().title()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM saved_locations WHERE LOWER(location) = LOWER(?)', (loc_clean,))
            conn.commit()
            return cursor.rowcount > 0

    def get_saved_locations(self):
        """Returns all bookmarked localities."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM saved_locations ORDER BY saved_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    def is_location_saved(self, location):
        """Checks if a location is currently bookmarked."""
        loc_clean = location.strip().title()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM saved_locations WHERE LOWER(location) = LOWER(?)', (loc_clean,))
            return cursor.fetchone() is not None

    def submit_feedback(self, location, category, comment):
        """Records a citizen safety observation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO safety_feedback (location, category, comment) VALUES (?, ?, ?)',
                (location.strip().title(), category.strip(), comment.strip())
            )
            conn.commit()
            return cursor.lastrowid

    def get_feedback_for_location(self, location, limit=10):
        """Fetches community safety observations for a specific locality."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM safety_feedback WHERE LOWER(location) = LOWER(?) ORDER BY submitted_at DESC LIMIT ?',
                (location.strip(), limit)
            )
            return [dict(row) for row in cursor.fetchall()]

