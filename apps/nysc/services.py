"""
NYSC Services & Tasks.
Phase 4 Module 10.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="records")
def export_nysc_data(self, session_id: str, batch: str):
    """
    Export eligible graduates for NYSC mobilisation.
    Generates Excel file in NYSC format.
    """
    from apps.nysc.models import NYSCEligibleGraduate, NYSCBatchExport
    from apps.institutional.models import AcademicSession
    import pandas as pd
    
    try:
        session = AcademicSession.objects.get(id=session_id)
    except AcademicSession.DoesNotExist:
        return {"status": "error", "message": "Session not found"}
    
    # Get eligible graduates
    graduates = NYSCEligibleGraduate.objects.filter(
        graduation_session=session,
        nysc_batch=batch,
    ).select_related("student")
    
    # Build dataframe
    data = []
    for g in graduates:
        data.append({
            "matric_no": g.student.matric_number,
            "surname": g.student.last_name,
            "first_name": g.student.first_name,
            "other_names": g.student.other_names,
            "dob": g.student.date_of_birth,
            "gender": g.student.gender,
            "state_of_origin": g.student.state_of_origin,
            "lga": g.student.lga_of_origin,
            "degree_class": g.degree_class,
            "cgpa": g.final_cgpa,
            "programme": g.student.programme.name,
            "graduation_year": session.name[:4],
            "batch": batch,
        })
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    from io import BytesIO
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    
    # Create export record
    export = NYSCBatchExport.objects.create(
        session=session,
        batch=batch,
        record_count=len(data),
    )
    
    # Would save to MinIO and update export_file
    
    return {
        "status": "success",
        "export_id": str(export.id),
        "record_count": len(data),
    }


def check_nysc_eligibility(student, session) -> dict:
    """
    Check if student is eligible for NYSC.
    """
    from apps.students.models import Student
    from datetime import date
    
    # Calculate age at graduation
    today = date.today()
    graduation_year = int(session.name[:4])
    
    age = graduation_year - student.date_of_birth.year if student.date_of_birth else 30
    
    return {
        "age_eligible": age < 30,
        "is_citizen": student.nationality == "Nigerian",
    }


def compute_degree_class(cgpa) -> str:
    """Compute degree class from CGPA."""
    if cgpa >= 4.5:
        return "First Class"
    elif cgpa >= 3.5:
        return "Second Class Upper"
    elif cgpa >= 2.4:
        return "Second Class Lower"
    elif cgpa >= 1.5:
        return "Third Class"
    else:
        return "Pass"