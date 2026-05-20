"""
ML API Schemas using Django Ninja.
Phase D - ML Inference endpoints.
"""

from ninja import Schema, Field
from typing import Optional, List
from pydantic import BaseModel, Field as PydanticField


# === D.3.2 CGPA Prediction Schema ===
class CGPAPredictIn(BaseModel):
    """Input for CGPA prediction."""
    student_id: str
    semester_1_gpa: float = Field(..., ge=0, le=5.0)
    semester_2_gpa: float = Field(..., ge=0, le=5.0)
    semester_3_gpa: Optional[float] = None
    semester_4_gpa: Optional[float] = None
    attendance_rate: float = Field(..., ge=0, le=100)
    course_load: int = Field(..., ge=0, le=30)
    library_visits: int = Field(..., ge=0)
    online_hours: float = Field(..., ge=0)


class CGPAPredictOut(BaseModel):
    """CGPA prediction output."""
    predicted_gpa: float
    confidence区间: float
    recommendation: str


# === D.5 Admissions Prediction ===
class AdmissionPredictIn(BaseModel):
    """Input for admissions prediction."""
    jamb_score: int = Field(..., ge=0, le=400)
    Jamb_subject_combo: str
    o_level_grades: str
    catchment_state: Optional[str] = None
    first_choice: bool = True
    screening_score: Optional[float] = None


class AdmissionPredictOut(BaseModel):
    """Admissions prediction output."""
    admission_probability: float
    cutoff_bracket: str
    recommended_courses: List[str]


# === D.1 Dropout Prediction ===
class DropoutPredictIn(BaseModel):
    """Input for dropout prediction."""
    student_id: str
    attendance_rate: float = Field(..., ge=0, le=100)
    gpa_trend: str  # "improving", "stable", "declining"
    financial_hold: bool = False
    credits_earned: int = Field(..., ge=0)
    credits_required: int = Field(..., ge=1)
    library_visits: int = Field(..., ge=0)
    online_activity: float = Field(..., ge=0)


class DropoutPredictOut(BaseModel):
    """Dropout prediction output."""
    dropout_risk: str  # "high", "medium", "low"
    risk_score: float
    interventions: List[str]


# === D.8 Face Recognition ===
class FaceVerifyIn(BaseModel):
    """Face verification input."""
    student_id: str
    image_base64: str


class FaceVerifyOut(BaseModel):
    """Face verification output."""
    matched: bool
    confidence: float


# === D.6 Plagiarism Detection ===
class PlagiarismCheckIn(BaseModel):
    """Plagiarism check input."""
    document_text: str
    course_id: Optional[str] = None


class PlagiarismCheckOut(BaseModel):
    """Plagiarism check output."""
    similarity_score: float
    sources: List[dict]
    flagged: bool


# === D.10 Transcript Search ===
class TranscriptSearchIn(BaseModel):
    """Transcript search input."""
    query: str
    filters: Optional[dict] = None


class TranscriptSearchOut(BaseModel):
    """Transcript search output."""
    results: List[dict]
    total: int