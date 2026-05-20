"""
SMS Notification Service - Termii + Twilio fallback.
Phase 1 Module 04.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class BulkSMSResult:
    """Result of bulk SMS sending."""
    total: int
    sent: int
    failed: int
    message_ids: list


class SMSException(Exception):
    """Base SMS exception."""
    pass


class TermiiClient:
    """
    Termii SMS Client (Primary - Naira priced, Nigerian).
    """
    
    BASE_URL = "https://api.termii.com/api"
    API_KEY = getattr(settings, "TERMII_API_KEY", "")
    SENDER_ID = getattr(settings, "TERMII_SENDER_ID", "UMIS-NG")
    USE_MOCK = getattr(settings, "TERMII_USE_MOCK", True)
    
    def send(self, phone: str, message: str, message_type: str = "plain") -> bool:
        """Send single SMS."""
        if self.USE_MOCK or not self.API_KEY:
            logger.info(f"[MOCK SMS] To: {phone}, Message: {message}")
            return True
        
        try:
            payload = {
                "api_key": self.API_KEY,
                "to": phone,
                "from": self.SENDER_ID,
                "sms": message,
                "type": message_type,
            }
            
            response = requests.post(
                f"{self.BASE_URL}/send",
                json=payload,
                timeout=30,
            )
            
            if response.status_code == 200:
                return True
            
            logger.error(f"Termii error: {response.status_code}")
            return False
            
        except requests.RequestException as exc:
            logger.error(f"Termii request failed: {exc}")
            return False
    
    def send_bulk(
        self,
        recipients: list[dict],
        message: str,
    ) -> BulkSMSResult:
        """Send bulk SMS."""
        total = len(recipients)
        failed = 0
        message_ids = []
        
        if self.USE_MOCK or not self.API_KEY:
            logger.info(f"[MOCK BULK SMS] {total} recipients")
            return BulkSMSResult(
                total=total,
                sent=total,
                failed=0,
                message_ids=[f"mock_{i}" for i in range(total)],
            )
        
        for recipient in recipients:
            phone = recipient.get("phone")
            if phone:
                success = self.send(phone, message)
                if success:
                    message_ids.append(phone)
                else:
                    failed += 1
        
        return BulkSMSResult(
            total=total,
            sent=total - failed,
            failed=failed,
            message_ids=message_ids,
        )


class TwilioClient:
    """
    Twilio SMS Client (Fallback - USD priced).
    """
    
    ACCOUNT_SID = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    AUTH_TOKEN = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    FROM_NUMBER = getattr(settings, "TWILIO_FROM_NUMBER", "")
    USE_MOCK = getattr(settings, "TWILIO_USE_MOCK", True)
    
    def send(self, phone: str, message: str) -> bool:
        """Send single SMS."""
        if self.USE_MOCK or not self.ACCOUNT_SID:
            logger.info(f"[MOCK TWILIO SMS] To: {phone}")
            return True
        
        try:
            from twilio.rest import Client
            
            client = Client(self.ACCOUNT_SID, self.AUTH_TOKEN)
            
            client.messages.create(
                body=message,
                from_=self.FROM_NUMBER,
                to=phone,
            )
            
            return True
            
        except Exception as exc:
            logger.error(f"Twilio error: {exc}")
            return False


class SMSService:
    """
    Primary SMS service with auto-failover.
    
    Primary: Termii (Naira-priced, Nigerian networks)
    Fallback: Twilio (USD, international)
    """
    
    # Failure tracking
    TERMII_FAILURES_KEY = "termii_failure_count"
    FAILOVER_THRESHOLD = 3
    
    def __init__(self):
        self.primary = TermiiClient()
        self.fallback = TwilioClient()
    
    def send(self, phone: str, message: str, message_type: str = "plain") -> bool:
        """Send SMS with automatic failover."""
        # Use fallback if Termii has failed multiple times
        if self._should_use_fallback():
            logger.info("Using Twilio fallback for SMS")
            return self.fallback.send(phone, message)
        
        # Try Termii first
        try:
            success = self.primary.send(phone, message, message_type)
            if success:
                self._record_termii_success()
                return True
            
            self._record_termii_failure()
            
            # Try fallback after Termii failure
            return self.fallback.send(phone, message)
            
        except Exception as exc:
            logger.error(f"SMS error: {exc}")
            self._record_termii_failure()
            return self.fallback.send(phone, message)
    
    def send_bulk(self, recipients: list[dict], message: str) -> BulkSMSResult:
        """Send bulk SMS."""
        if self._should_use_fallback():
            logger.info("Using Twilio fallback for bulk SMS")
            return self.fallback.send_bulk(recipients, message)
        
        try:
            result = self.primary.send_bulk(recipients, message)
            if result.failed > 0:
                self._record_termii_failure()
            else:
                self._record_termii_success()
            return result
            
        except Exception as exc:
            logger.error(f"Bulk SMS error: {exc}")
            self._record_termii_failure()
            return self.fallback.send_bulk(recipients, message)
    
    def _should_use_fallback(self) -> bool:
        """Check if we should skip Termii."""
        failures = cache.get(self.TERMII_FAILURES_KEY, 0)
        return failures >= self.FAILOVER_THRESHOLD
    
    def _record_termii_failure(self):
        """Record Termii failure."""
        failures = cache.get(self.TERMII_FAILURES_KEY, 0) + 1
        cache.set(self.TERMII_FAILURES_KEY, failures, 3600)  # 1 hour
    
    def _record_termii_success(self):
        """Record Termii success - reset counter."""
        cache.delete(self.TERMII_FAILURES_KEY)


# Notification Templates
NOTIFICATION_TEMPLATES = {
    "admission_offer": (
        "Congratulations {name}! You have been offered admission to study {programme} "
        "at {university}. Your offer expires {date}. "
        "Login at {url} to accept."
    ),
    "jamb_verified": (
        "{name}, your JAMB verification is complete. "
        "Your score: {score}. "
        "Next steps: {next_steps}"
    ),
    "matric_number": (
        "{name}, your matriculation number is {matric}. "
        "Welcome to {university}!"
    ),
    "admission_reminder": (
        "{name}, reminder: Your admission offer for {programme} "
        "expires on {date}. Accept now at {url}"
    ),
    "result_release": (
        "{name}, your {semester} results are now available. "
        "Log in to view: {url}"
    ),
}


def send_admission_offer_sms(
    phone: str,
    name: str,
    programme: str,
    university: str,
    deadline: str,
    url: str,
) -> bool:
    """Send admission offer notification."""
    template = NOTIFICATION_TEMPLATES["admission_offer"]
    message = template.format(
        name=name,
        programme=programme,
        university=university,
        date=deadline,
        url=url,
    )
    
    service = SMSService()
    return service.send(phone, message)


def send_matric_number_sms(
    phone: str,
    name: str,
    matric: str,
    university: str,
) -> bool:
    """Send matriculation number notification."""
    template = NOTIFICATION_TEMPLATES["matric_number"]
    message = template.format(
        name=name,
        matric=matric,
        university=university,
    )
    
    service = SMSService()
    return service.send(phone, message)


# Singleton
_sms_service = None


def get_sms_service() -> SMSService:
    """Get singleton SMS service."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service