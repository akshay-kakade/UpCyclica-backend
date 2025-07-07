from fastapi import FastAPI, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import random
from fastapi.middleware.cors import CORSMiddleware
from db import Base, engine, SessionLocal
from models import WasteSubmission
from uuid import uuid4

app = FastAPI()

# ✅ Auto-create tables
Base.metadata.create_all(bind=engine)

# ✅ Allow frontend access (adjust in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request schema
class WasteInput(BaseModel):
    description: str
    file_url: Optional[str] = None
    waste_type: Optional[str] = None
    source: Optional[str] = None
    batch_weight: Optional[float] = None
    notes: Optional[str] = None
    location: Optional[str] = None

# ✅ Basic ML classifier (random logic for now)
def classify_waste(text: str):
    categories = [
        "Fruits & Vegetables",
        "Grains & Breads",
        "Meat & Dairy",
        "Cooked Waste",
        "Expired Packaged",
        "Oil & Fat"
    ]
    suggestions = {
        "Fruits & Vegetables": "Compost or Animal Feed",
        "Grains & Breads": "Compost or Fermentation",
        "Meat & Dairy": "Biofuel or Anaerobic Digestion",
        "Cooked Waste": "Anaerobic Digestion or Biogas",
        "Expired Packaged": "Manual sort + Biofuel",
        "Oil & Fat": "Biodiesel Conversion"
    }

    category = random.choice(categories)
    return {
        "category": category,
        "suggested_method": suggestions[category],
        "roi_estimate": f"${random.randint(5, 30)}",
        "co2_saved_kg": round(random.uniform(1.0, 10.0), 2)
    }

# ✅ Show GET for sanity
@app.get("/submit")
def show_submit_info():
    return {"message": "POST to /submit with waste data"}

# ✅ Classifier-only endpoint (no DB save)
@app.post("/classify")
def classify_only(input: WasteInput):
    result = classify_waste(input.description)
    return {
        "input": input,
        "classification": result
    }

# ✅ Store submission in DB with classification
@app.post("/submit")
def classify_and_save(input: WasteInput, authorization: Optional[str] = Header(None)):
    result = classify_waste(input.description)

    # TODO: Replace with real Clerk user ID
    user_id = "mock_user_123"

    db = SessionLocal()
    submission = WasteSubmission(
        id=str(uuid4()),
        user_id=user_id,
        description=input.description,
        file_url=input.file_url,
        category=result["category"],
        suggested_method=result["suggested_method"],
        roi_estimate=result["roi_estimate"],
        co2_saved_kg=result["co2_saved_kg"],
        waste_type=input.waste_type,
        source=input.source,
        batch_weight=input.batch_weight,
        notes=input.notes,
        location=input.location
    )
    db.add(submission)
    db.commit()
    db.close()

    return {
        "input": input,
        "classification": result
    }

# ✅ Dependency for DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Get all submissions (with new fields)
@app.get("/submissions")
def get_submissions(user_id: Optional[str] = "mock_user_123", db: Session = Depends(get_db)):
    submissions = (
        db.query(WasteSubmission)
        .filter(WasteSubmission.user_id == user_id)
        .order_by(WasteSubmission.created_at.desc())
        .all()
    )
    results = [{
        "id": s.id,
        "description": s.description,
        "file_url": s.file_url,
        "category": s.category,
        "suggested_method": s.suggested_method,
        "roi_estimate": s.roi_estimate,
        "co2_saved_kg": s.co2_saved_kg,
        "created_at": s.created_at.isoformat(),
        "waste_type": s.waste_type,
        "source": s.source,
        "batch_weight": s.batch_weight,
        "notes": s.notes,
        "location": s.location,
    } for s in submissions]

    return JSONResponse(content={"submissions": results})

# ✅ Get clusters by waste type and source
@app.get("/insights/by-type-source")
def cluster_by_type_source(user_id: Optional[str] = "mock_user_123", db: Session = Depends(get_db)):
    submissions = db.query(WasteSubmission).filter(WasteSubmission.user_id == user_id).all()

    grouped = {}
    for s in submissions:
        key = (s.waste_type or "Unknown", s.source or "Unknown")
        if key not in grouped:
            grouped[key] = {"count": 0, "total_weight": 0.0}
        grouped[key]["count"] += 1
        grouped[key]["total_weight"] += s.batch_weight or 0.0

    return grouped

from fastapi import HTTPException

@app.delete("/delete/{submission_id}")
def delete_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(WasteSubmission).filter(WasteSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    db.delete(submission)
    db.commit()
    return {"message": "Deleted successfully", "id": submission_id}

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "🚀 FastAPI running on Railway"}
