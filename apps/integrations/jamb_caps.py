"""
JAMB CAPS Integration Client.
Phase 1 Module 02.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# Circuit breaker settings
CIRCUIT_BREAKER_KEY = "jamb_caps_circuit_breaker"
CIRCUIT_BREAKER_THRESHOLD = 10
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes


class JAMBCAPSException(Exception):
    """Base exception for JAMB CAPS errors."""
    pass


class JAMBVerificationFailed(JAMBCAPSException):
    """JAMB verification failed."""
    pass


class JAMBServiceUnavailable(JAMBCAPSException):
    """JAMB CAPS service is unavailable."""
    pass


@dataclass
class JAMBVerificationResult:
    """JAMB verification result."""
    jamb_reg_no: str
    utme_score: int
    photo_url: str
    date_of_birth: Optional[date] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    state: Optional[str] = None
    lga: Optional[str] = None
    subjects: Optional[list] = None


class CircuitBreaker:
    """Circuit breaker pattern for API resilience."""
    
    def __init__(self, key: str, threshold: int = 10, timeout: int = 300):
        self.key = f"circuit_{key}"
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
    
    def record_failure(self):
        """Record a failure."""
        self.failures = cache.get(self.key, 0) + 1
        cache.set(self.key, self.failures, self.timeout)
    
    def record_success(self):
        """Record success - reset counter."""
        cache.delete(self.key)
        self.failures = 0
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        failures = cache.get(self.key, 0)
        return failures >= self.threshold
    
    def reset(self):
        """Manually reset circuit breaker."""
        cache.delete(self.key)
        self.failures = 0


# Global circuit breaker
_circuit_breaker = CircuitBreaker(CIRCUIT_BREAKER_KEY, CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT)


class JAMBCAPSClient:
    """
    JAMB Central Admissions Processing System (CAPS) client.
    
    Mock client available for test/development environments.
    """
    
    BASE_URL = getattr(settings, "JAMB_CAPS_URL", "https://caps.jamb.gov.ng/api")
    API_KEY = getattr(settings, "JAMB_CAPS_API_KEY", "")
    INSTITUTION_CODE = getattr(settings, "JAMB_INSTITUTION_CODE", "")
    USE_MOCK = getattr(settings, "JAMB_USE_MOCK", True)  # Default to mock
    
    def __init__(self):
        self.use_mock = self.USE_MOCK or not self.API_KEY
    
    def verify(self, jamb_reg_no: str) -> JAMBVerificationResult:
        """
        Verify JAMB registration number and get candidate details.
        
        Args:
            jamb_reg_no: JAMB registration number
            
        Returns:
            JAMBVerificationResult with score, photo, etc.
            
        Raises:
            JAMBVerificationFailed: If verification fails
            JAMBServiceUnavailable: If service is down
        """
        if _circuit_breaker.is_open():
            raise JAMBServiceUnavailable(
                "JAMB CAPS service unavailable due to repeated failures"
            )
        
        if self.use_mock:
            return self._mock_verify(jamb_reg_no)
        
        try:
            return self._api_verify(jamb_reg_no)
        except requests.RequestException as exc:
            _circuit_breaker.record_failure()
            logger.error(f"JAMB API error: {exc}")
            raise JAMBServiceUnavailable(f"JAMB service unavailable: {exc}")
        except Exception as exc:
            _circuit_breaker.record_failure()
            logger.error(f"JAMB verification error: {exc}")
            raise JAMBVerificationFailed(str(exc))
    
    def _mock_verify(self, jamb_reg_no: str) -> JAMBVerificationResult:
        """Mock verification for test/development."""
        # Generate consistent but random-looking score based on reg number
        score = (hash(jamb_reg_no) % 280) + 120  # Range: 120-400
        
        return JAMBVerificationResult(
            jamb_reg_no=jamb_reg_no,
            utme_score=score,
            photo_url=f"https://example.com/photos/{jamb_reg_no}.jpg",
            date_of_birth=date(2005, 1, 15),
            first_name="Test",
            last_name="Candidate",
            middle_name="Middle",
            state="Lagos",
            lga="Alimosho",
            subjects=[
                {"name": "English", "score": score - 50},
                {"name": "Mathematics", "score": score - 80},
                {"name": "Physics", "score": score - 100},
                {"name": "Chemistry", "score": score - 90},
            ],
        )
    
    def _api_verify(self, jamb_reg_no: str) -> JAMBVerificationResult:
        """Real API verification."""
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "reg_no": jamb_reg_no,
            "institution_code": self.INSTITUTION_CODE,
        }
        
        response = requests.post(
            f"{self.BASE_URL}/verify",
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        if response.status_code == 503:
            raise JAMBServiceUnavailable("JAMB service unavailable")
        
        if response.status_code != 200:
            raise JAMBVerificationFailed(
                f"Verification failed: {response.status_code}"
            )
        
        data = response.json()
        
        return JAMBVerificationResult(
            jamb_reg_no=jamb_reg_no,
            utme_score=data.get("utme_score", 0),
            photo_url=data.get("photo_url", ""),
            date_of_birth=data.get("date_of_birth"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            middle_name=data.get("middle_name"),
            state=data.get("state"),
            lga=data.get("lga"),
            subjects=data.get("subjects", []),
        )
    
    def confirm_admission(
        self,
        jamb_reg_no: str,
        programme: str,
        session: str,
    ) -> bool:
        """
        Confirm admission in CAPS.
        
        Args:
            jamb_reg_no: JAMB registration number
            programme: Programme code
            session: Academic session
            
        Returns:
            True if confirmation successful
        """
        if self.use_mock:
            return True
        
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "reg_no": jamb_reg_no,
            "programme": programme,
            "session": session,
            "institution_code": self.INSTITUTION_CODE,
        }
        
        response = requests.post(
            f"{self.BASE_URL}/confirm",
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        return response.status_code == 200


# Singleton instance
_jamb_client = None


def get_jamb_client() -> JAMBCAPSClient:
    """Get singleton JAMB client instance."""
    global _jamb_client
    if _jamb_client is None:
        _jamb_client = JAMBCAPSClient()
    return _jamb_client