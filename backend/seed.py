# File: backend/seed.py

import os
from datetime import datetime, timedelta

from backend.database import IS_POSTGRES, init_db, get_db_connection, get_db_cursor

def seed_db():
    # Make sure tables exist
    init_db()
    
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    
    # Check if we already have inquiries or bookings to avoid double-seeding
    cursor.execute("SELECT COUNT(*) AS total FROM inquiries")
    row = cursor.fetchone()
    
    # Handle dict (Postgres RealDictCursor) vs tuple (SQLite) return values
    count = row["total"] if isinstance(row, dict) else row[0]
    
    if count > 0:
        print("Database already contains data. Skipping seed.")
        conn.close()
        return
        
    print("Seeding database with sample inquiries and bookings...")
    
    # Base date calculations (May 2026)
    today = datetime(2026, 5, 21)
    
    mock_inquiries = [
        {
            "name": "Arjun Nair",
            "email": "arjun.nair@gmail.com",
            "phone": "+919876543210",
            "event_date": "2026-05-24",
            "event_type": "wedding",
            "guest_count": 500,
            "ac_option": "ac",
            "notes": "Wedding reception with traditional Kerala lunch (Sadhya). Stage decorations are critical.",
            "status": "approved",
            "created_at": (today - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Malabar Tech Solutions",
            "email": "events@malabartech.com",
            "phone": "+918899001122",
            "event_date": "2026-05-28",
            "event_type": "corporate",
            "guest_count": 250,
            "ac_option": "ac",
            "notes": "Annual team symposium. Need high-speed internet, projector access, and catering setup space.",
            "status": "pending",
            "created_at": (today - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Fathima R.",
            "email": "fathima.r@yahoo.com",
            "phone": "+919944556677",
            "event_date": "2026-06-05",
            "event_type": "wedding",
            "guest_count": 600,
            "ac_option": "ac",
            "notes": "Nikah Ceremony & Reception. Needs dressing/green room access early morning.",
            "status": "approved",
            "created_at": (today - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Lions Club Alleppey",
            "email": "alleppeylions@gmail.com",
            "phone": "+914772251122",
            "event_date": "2026-06-14",
            "event_type": "party",
            "guest_count": 150,
            "ac_option": "non-ac",
            "notes": "Charity dinner and cultural program. Audio setup needed.",
            "status": "approved",
            "created_at": (today - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Devanand S.",
            "email": "devanand@outlook.com",
            "phone": "+919000111222",
            "event_date": "2026-06-20",
            "event_type": "other",
            "guest_count": 350,
            "ac_option": "non-ac",
            "notes": "Shashti Poorthi (60th Birthday Celebration). Traditional music troupe setup.",
            "status": "pending",
            "created_at": today.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Alleppey Tourism Forum",
            "email": "info@alleppeytourism.org",
            "phone": "+914772200300",
            "event_date": "2026-07-12",
            "event_type": "corporate",
            "guest_count": 400,
            "ac_option": "ac",
            "notes": "Tourism development council meet. Panelists require mic setups.",
            "status": "approved",
            "created_at": (today - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # 1. Insert mock inquiries and match their booking states
    for inq in mock_inquiries:
        if IS_POSTGRES:
            cursor.execute("""
                INSERT INTO inquiries (name, email, phone, event_date, event_type, guest_count, ac_option, notes, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                inq["name"], inq["email"], inq["phone"], inq["event_date"],
                inq["event_type"], inq["guest_count"], inq["ac_option"],
                inq["notes"], inq["status"], inq["created_at"]
            ))
            inquiry_id = cursor.fetchone()["id"]
        else:
            cursor.execute("""
                INSERT INTO inquiries (name, email, phone, event_date, event_type, guest_count, ac_option, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inq["name"], inq["email"], inq["phone"], inq["event_date"],
                inq["event_type"], inq["guest_count"], inq["ac_option"],
                inq["notes"], inq["status"], inq["created_at"]
            ))
            inquiry_id = cursor.lastrowid
        
        # 2. Insert into bookings matching the inquiry state
        booking_status = "booked" if inq["status"] == "approved" else "pending"
        
        if IS_POSTGRES:
            cursor.execute("""
                INSERT INTO bookings (date, status, inquiry_id)
                VALUES (%s, %s, %s)
            """, (inq["event_date"], booking_status, inquiry_id))
        else:
            cursor.execute("""
                INSERT INTO bookings (date, status, inquiry_id)
                VALUES (?, ?, ?)
            """, (inq["event_date"], booking_status, inquiry_id))
        
    # Add a manual block for maintenance
    if IS_POSTGRES:
        cursor.execute("""
            INSERT INTO bookings (date, status, inquiry_id)
            VALUES ('2026-05-30', 'booked', NULL)
            ON CONFLICT (date) DO NOTHING
        """)
    else:
        cursor.execute("""
            INSERT OR IGNORE INTO bookings (date, status, inquiry_id)
            VALUES ('2026-05-30', 'booked', NULL)
        """)
    
    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_db()
