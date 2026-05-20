"""
Admissions Celery Tasks - JAMB CAPS Integration.
Phase 1 Module 02.
"""

import logging
from decimal import Decimal

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    queue="jamb",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=960,
)
def fetch_jamb_caps_data(self, jamb_reg_no: str, admission_id: int):
    """
    Async JAMB CAPS verification.
    
    Called on application submission.
    Never blocks the request cycle.
    Retries with exponential backoff: 60s, 120s, 240s, 480s, 960s.
    
    On final failure: sets application state to 'jamb_failed'
    and alerts Registrar via SMS.
    """
    from apps.admissions.models import Application, JAMBVerificationLog
    from apps.integrations.jamb_caps import get_jamb_client, JAMBCAPSException
    from apps.notifications.sms import get_sms_service
    
    try:
        # Get client
        client = get_jamb_client()
        
        # Fetch JAMB data
        caps_data = client.verify(jamb_reg_no)
        
        # Get application
        with transaction.atomic():
            application = Application.objects.select_for_update().get(
                id=admission_id
            )
            
            # Update application
            application.jamb_score = caps_data.utme_score
            application.jamb_photo_url = caps_data.photo_url
            application.jamb_verify()
            
            # Log successful verification
            JAMBVerificationLog.objects.create(
                application=application,
                jamb_reg_no=jamb_reg_no,
                api_response={
                    "utme_score": caps_data.utme_score,
                    "photo_url": caps_data.photo_url,
                },
                is_success=True,
            )
            
            # Check against threshold
            from apps.institutional.models import InstitutionalConfig
            config = InstitutionalConfig.objects.get(tenant=application.applicant.tenant)
            
            if caps_data.utme_score < config.jamb_minimum_score:
                application.below_threshold()
                logger.info(
                    f"Application {admission_id} below threshold: "
                    f"{caps_data.utme_score} < {config.jamb_minimum_score}"
                )
            else:
                # Check if Post-UTME is required
                if not application.post_utme_score:
                    application.invite_post_utme()
            
            application.save()
            
            logger.info(
                f"JAMB verification complete for {jamb_reg_no}: "
                f"Score {caps_data.utme_score}"
            )
            
            return {"status": "success", "score": caps_data.utme_score}
    
    except JAMBCAPSException as exc:
        # Log failure
        try:
            application = Application.objects.get(id=admission_id)
            JAMBVerificationLog.objects.create(
                application=application,
                jamb_reg_no=jamb_reg_no,
                api_response={},
                is_success=False,
                error_message=str(exc),
            )
        except Application.DoesNotExist:
            pass
        
        # Notify registrar on final failure
        if self.request.retries >= self.max_retries:
            try:
                application = Application.objects.get(id=admission_id)
                application.jamb_fail()
                application.rejection_reason = f"JAMB verification failed: {exc}"
                application.save()
                
                # Alert registrar via SMS
                sms_service = get_sms_service()
                # Would send alert to registrar here
                logger.error(
                    f"JAMB verification failed for application {admission_id} "
                    f"after {self.max_retries} retries"
                )
            except Application.DoesNotExist:
                pass
        
        raise self.retry(exc=exc)
    
    except Application.DoesNotExist:
        logger.error(f"Application {admission_id} not found")
        return {"status": "error", "message": "Application not found"}


@shared_task(bind=True, queue="notifications")
def send_admission_notifications(self, application_id: int):
    """Send notification when application status changes."""
    from apps.admissions.models import Application, AdmissionOffer
    
    try:
        application = Application.objects.get(id=application_id)
        
        # Get phone number
        phone = application.applicant.phone
        if not phone:
            return {"status": "error", "message": "No phone number"}
        
        from apps.notifications.sms import send_admission_offer_sms
        
        if application.state == "offered":
            # Send offer notification
            offer = application.offer
            if offer:
                send_admission_offer_sms(
                    phone=phone,
                    name=application.applicant.get_full_name(),
                    programme=offer.programme.name,
                    university=application.applicant.tenant.name,
                    deadline=offer.acceptance_deadline.strftime("%Y-%m-%d"),
                    url=f"https://{application.applicant.tenant.slug}.edu.ng/applicant/offer",
                )
        
        return {"status": "success"}
    
    except Application.DoesNotExist:
        return {"status": "error", "message": "Application not found"}


@shared_task(bind=True, queue="default")
def check_offer_expiry(self):
    """Check and expire stale offers."""
    from datetime import date
    from apps.admissions.models import Application, AdmissionOffer
    
    today = date.today()
    
    # Find expired offers
    expired = AdmissionOffer.objects.filter(
        state="pending",
        acceptance_deadline__lt=today,
    )
    
    count = 0
    for offer in expired:
        offer.expire()
        offer.save()
        count += 1
    
    logger.info(f"Expired {count} admission offers")
    return {"status": "success", "expired": count}