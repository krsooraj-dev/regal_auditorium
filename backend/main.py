import os
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

from backend.database import (
    init_db,
    get_bookings_for_month,
    create_inquiry,
    get_inquiries,
    update_inquiry_status,
    toggle_manual_booking
)

app = FastAPI(title="Regal Auditorium Digital Platform API")

# Initialize Database on Startup
@app.on_event("startup")
def startup_event():
    init_db()

# --- Pydantic Models ---
class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    phone: str = Field(..., min_length=10, max_length=15)
    event_date: str  # Format: YYYY-MM-DD
    event_type: str
    guest_count: int = Field(..., gt=0)
    ac_option: str
    notes: Optional[str] = ""

class StatusUpdate(BaseModel):
    status: str  # 'approved', 'declined', 'archived', 'pending'

class ManualBlock(BaseModel):
    date: str  # Format: YYYY-MM-DD
    status: str  # 'booked', 'pending', 'available'

# --- API Endpoints ---

@app.get("/api/availability")
def get_availability(year: int = Query(..., ge=2020), month: int = Query(..., ge=1, le=12)):
    """
    Returns booking statuses for the specified month and year.
    Returns mapping like: {"2026-05-15": "booked", "2026-05-20": "pending"}
    """
    try:
        data = get_bookings_for_month(year, month)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inquiries")
def post_inquiry(inquiry: InquiryCreate):
    """
    Submits a booking inquiry and sets the date status as 'pending' in bookings.
    """
    # Simple date validation
    try:
        datetime.strptime(inquiry.event_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    try:
        inquiry_id = create_inquiry(
            name=inquiry.name,
            email=inquiry.email,
            phone=inquiry.phone,
            event_date=inquiry.event_date,
            event_type=inquiry.event_type,
            guest_count=inquiry.guest_count,
            ac_option=inquiry.ac_option,
            notes=inquiry.notes
        )
        return {"status": "success", "message": "Inquiry submitted successfully.", "inquiry_id": inquiry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/inquiries")
def get_all_inquiries():
    """
    Retrieves all booking inquiries, ordered by date submitted (descending).
    """
    try:
        inquiries = get_inquiries()
        return {"status": "success", "data": inquiries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/inquiries/{inquiry_id}")
def update_inquiry(inquiry_id: int, update_data: StatusUpdate):
    """
    Update inquiry status. Approving it changes the associated booking date to 'booked'.
    """
    if update_data.status not in ["approved", "declined", "archived", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be approved, declined, archived, or pending.")
        
    try:
        success = update_inquiry_status(inquiry_id, update_data.status)
        if not success:
            raise HTTPException(status_code=404, detail="Inquiry not found.")
        return {"status": "success", "message": f"Inquiry status updated to {update_data.status}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/bookings/block")
def block_date(block: ManualBlock):
    """
    Manually override booking status for a specific date.
    """
    try:
        datetime.strptime(block.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    if block.status not in ["booked", "pending", "available"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be booked, pending, or available.")
        
    try:
        toggle_manual_booking(block.date, block.status)
        return {"status": "success", "message": f"Date {block.date} updated to {block.status}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Static Files Serving ---

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(ROOT_DIR, "index.html"))

@app.get("/pages/{page_name}")
def serve_page(page_name: str):
    page_path = os.path.join(ROOT_DIR, "pages", page_name)
    if os.path.exists(page_path):
        return FileResponse(page_path)
    # Fallback to index if subpage not found (or return 404)
    raise HTTPException(status_code=404, detail="Page not found")

# Mount CSS, JS, and Images folders
app.mount("/css", StaticFiles(directory=os.path.join(ROOT_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(ROOT_DIR, "js")), name="js")
app.mount("/images", StaticFiles(directory=os.path.join(ROOT_DIR, "images")), name="images")
