# File: backend/database.py

import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Render sometimes injects postgres:// instead of postgresql://. Let's fix that.
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = DATABASE_URL is not None

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "bookings.db")

def get_db_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    return conn

def get_db_cursor(conn):
    if IS_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def init_db():
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    
    if IS_POSTGRES:
        # Create inquiries table in Postgres
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inquiries (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                event_date VARCHAR(20) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                guest_count INTEGER NOT NULL,
                ac_option VARCHAR(50) NOT NULL,
                notes TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create bookings table in Postgres
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                date VARCHAR(20) UNIQUE NOT NULL,
                status VARCHAR(50) NOT NULL,
                inquiry_id INTEGER REFERENCES inquiries(id) ON DELETE SET NULL
            )
        """)
    else:
        # Create inquiries table in SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                guest_count INTEGER NOT NULL,
                ac_option TEXT NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create bookings table in SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                inquiry_id INTEGER,
                FOREIGN KEY (inquiry_id) REFERENCES inquiries(id) ON DELETE SET NULL
            )
        """)
        
    conn.commit()
    conn.close()

def get_bookings_for_month(year: int, month: int):
    """
    Returns a dict of date_str: status mapping for a specific year and month
    e.g., {"2026-05-15": "booked", "2026-05-18": "pending"}
    """
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    month_str = f"{year:04d}-{month:02d}-%"
    
    if IS_POSTGRES:
        cursor.execute(
            "SELECT date, status FROM bookings WHERE date LIKE %s", 
            (month_str,)
        )
    else:
        cursor.execute(
            "SELECT date, status FROM bookings WHERE date LIKE ?", 
            (month_str,)
        )
    rows = cursor.fetchall()
    conn.close()
    
    return {row["date"]: row["status"] for row in rows}

def create_inquiry(name: str, email: str, phone: str, event_date: str, 
                   event_type: str, guest_count: int, ac_option: str, notes: str = ""):
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    
    try:
        # 1. Insert into inquiries
        if IS_POSTGRES:
            cursor.execute("""
                INSERT INTO inquiries (name, email, phone, event_date, event_type, guest_count, ac_option, notes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                RETURNING id
            """, (name, email, phone, event_date, event_type, guest_count, ac_option, notes))
            inquiry_id = cursor.fetchone()["id"]
        else:
            cursor.execute("""
                INSERT INTO inquiries (name, email, phone, event_date, event_type, guest_count, ac_option, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (name, email, phone, event_date, event_type, guest_count, ac_option, notes))
            inquiry_id = cursor.lastrowid
        
        # 2. Insert as a 'pending' slot in bookings if the date isn't already booked
        if IS_POSTGRES:
            cursor.execute("SELECT status FROM bookings WHERE date = %s", (event_date,))
        else:
            cursor.execute("SELECT status FROM bookings WHERE date = ?", (event_date,))
        existing = cursor.fetchone()
        
        if not existing:
            if IS_POSTGRES:
                cursor.execute("""
                    INSERT INTO bookings (date, status, inquiry_id)
                    VALUES (%s, 'pending', %s)
                """, (event_date, inquiry_id))
            else:
                cursor.execute("""
                    INSERT INTO bookings (date, status, inquiry_id)
                    VALUES (?, 'pending', ?)
                """, (event_date, inquiry_id))
        elif existing["status"] == "pending":
            if IS_POSTGRES:
                cursor.execute("""
                    UPDATE bookings SET inquiry_id = %s WHERE date = %s
                """, (inquiry_id, event_date))
            else:
                cursor.execute("""
                    UPDATE bookings SET inquiry_id = ? WHERE date = ?
                """, (inquiry_id, event_date))
            
        conn.commit()
        return inquiry_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_inquiries():
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    cursor.execute("SELECT * FROM inquiries ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    inquiries_list = []
    for row in rows:
        inquiries_list.append(dict(row))
    return inquiries_list

def update_inquiry_status(inquiry_id: int, status: str):
    """
    Updates the inquiry status. If approved, marks the date as 'booked'.
    If declined or archived, removes the booking slot (unless it was manually blocked).
    """
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    
    try:
        # Get the inquiry details
        if IS_POSTGRES:
            cursor.execute("SELECT event_date, status FROM inquiries WHERE id = %s", (inquiry_id,))
        else:
            cursor.execute("SELECT event_date, status FROM inquiries WHERE id = ?", (inquiry_id,))
        inquiry = cursor.fetchone()
        if not inquiry:
            return False
            
        old_status = inquiry["status"]
        event_date = inquiry["event_date"]
        
        # Update inquiry status
        if IS_POSTGRES:
            cursor.execute("UPDATE inquiries SET status = %s WHERE id = %s", (status, inquiry_id))
        else:
            cursor.execute("UPDATE inquiries SET status = ? WHERE id = ?", (status, inquiry_id))
        
        if status == "approved":
            # Mark the date as fully booked
            if IS_POSTGRES:
                cursor.execute("""
                    INSERT INTO bookings (date, status, inquiry_id)
                    VALUES (%s, 'booked', %s)
                    ON CONFLICT (date) DO UPDATE SET status = 'booked', inquiry_id = EXCLUDED.inquiry_id
                """, (event_date, inquiry_id))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO bookings (date, status, inquiry_id)
                    VALUES (?, 'booked', ?)
                """, (event_date, inquiry_id))
        elif status in ["declined", "archived"]:
            # If we are declining or archiving, and the booking was tied to this inquiry,
            # we should remove it, unless another inquiry is approved for it.
            if IS_POSTGRES:
                cursor.execute("SELECT id FROM bookings WHERE date = %s AND inquiry_id = %s", (event_date, inquiry_id))
                matching_booking = cursor.fetchone()
                if matching_booking:
                    cursor.execute("DELETE FROM bookings WHERE date = %s AND inquiry_id = %s", (event_date, inquiry_id))
            else:
                cursor.execute("SELECT id FROM bookings WHERE date = ? AND inquiry_id = ?", (event_date, inquiry_id))
                matching_booking = cursor.fetchone()
                if matching_booking:
                    cursor.execute("DELETE FROM bookings WHERE date = ? AND inquiry_id = ?", (event_date, inquiry_id))
                
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def toggle_manual_booking(date_str: str, status: str):
    """
    Manually block or clear a date.
    status can be 'booked', 'pending', or 'available' (which deletes the block).
    """
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    
    try:
        if status == "available":
            if IS_POSTGRES:
                cursor.execute("DELETE FROM bookings WHERE date = %s", (date_str,))
            else:
                cursor.execute("DELETE FROM bookings WHERE date = ?", (date_str,))
        else:
            if IS_POSTGRES:
                cursor.execute("""
                    INSERT INTO bookings (date, status, inquiry_id)
                    VALUES (%s, %s, NULL)
                    ON CONFLICT (date) DO UPDATE SET status = EXCLUDED.status, inquiry_id = NULL
                """, (date_str, status))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO bookings (date, status, inquiry_id)
                    VALUES (?, ?, NULL)
                """, (date_str, status))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
