"""
O-Level OCR Extraction Service.
Phase 6 - AI Domain 5.1.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OLevelExtractionResult:
    """O-Level extraction result."""
    subjects: List[dict]
    confidence: float
    requires_manual_review: bool
    raw_text: str


def extract_olevel_results(image_bytes: bytes, student_id: str) -> OLevelExtractionResult:
    """
    Extract O-Level results from image.
    
    1. Pillow: deskew, contrast enhancement, binarization
    2. Tesseract: OCR → raw text
    3. spaCy: NER to extract subject/grade pairs
    4. Validation: at least 5 subjects, English mandatory
    5. Return result
    """
    # This is a simplified placeholder
    # Production would use:
    # - Pillow for image preprocessing
    # - pytesseract for OCR
    # - spaCy for NER
    
    # Placeholder extraction
    subjects = [
        {"subject": "English Language", "grade": "C4"},
        {"subject": "Mathematics", "grade": "B2"},
        {"subject": "Physics", "grade": "B3"},
        {"subject": "Chemistry", "grade": "C4"},
        {"subject": "Biology", "grade": "C5"},
    ]
    
    return OLevelExtractionResult(
        subjects=subjects,
        confidence=0.85,
        requires_manual_review=False,
        raw_text="Extracted text...",
    )


def validate_olevel_subjects(subjects: List[dict]) -> tuple[bool, List[str]]:
    """Validate O-Level subjects meet requirements."""
    errors = []
    
    if len(subjects) < 5:
        errors.append("At least 5 subjects required")
    
    # Check for English
    has_english = any(
        "english" in s.get("subject", "").lower() 
        for s in subjects
    )
    if not has_english:
        errors.append("English Language is mandatory")
    
    # Check for valid grades
    valid_grades = ["A1", "A2", "A3", "B4", "B5", "B6", "C4", "C5", "C6", "D7", "E8", "F9"]
    for s in subjects:
        grade = s.get("grade", "")
        if grade not in valid_grades:
            errors.append(f"Invalid grade: {grade}")
    
    return len(errors) == 0, errors