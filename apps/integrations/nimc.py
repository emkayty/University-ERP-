"""
NIMC NIN Verification Client.
Phase 1 Module 03.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class NIMCException(Exception):
    """Base exception for NIMC errors."""
    pass


class NIMCVerificationFailed(NIMCException):
    """NIN verification failed."""
    pass


class NIMCServiceUnavailable(NIMCException):
    """NIMC service unavailable."""
    pass


@dataclass
class NIMCVerificationResult:
    """NIMC verification result."""
    nin: str
    first_name: str
    last_name: str
    middle_name: str
    date_of_birth: date
    gender: str
    state: str
    lga: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_verified: bool = True


class NIMCClient:
    """
    NIMC NIN Verification Client.
    Uses NIMC's public verification API.
    """
    
    BASE_URL = getattr(settings, "NIMC_API_URL", "https://api.nimc.gov.ng/api/v2")
    API_KEY = getattr(settings, "NIMC_API_KEY", "")
    USE_MOCK = getattr(settings, "NIMC_USE_MOCK", True)
    
    def verify_nin(
        self,
        nin: str,
        first_name: str,
        last_name: str,
        dob: date,
    ) -> NIMCVerificationResult:
        """
        Verify NIN against provided details.
        
        Args:
            nin: 11-digit NIN
            first_name: First name as on NIN
            last_name: Last name as on NIN
            dob: Date of birth
            
        Returns:
            NIMCVerificationResult
            
        Raises:
            NIMCVerificationFailed: If verification fails
            NIMCServiceUnavailable: If service is down
        """
        if self.USE_MOCK or not self.API_KEY:
            return self._mock_verify(nin, first_name, last_name, dob)
        
        try:
            return self._api_verify(nin, first_name, last_name, dob)
        except requests.RequestException as exc:
            logger.error(f"NIMC API error: {exc}")
            raise NIMCServiceUnavailable(f"NIMC service unavailable: {exc}")
        except Exception as exc:
            logger.error(f"NIMC verification error: {exc}")
            raise NIMCVerificationFailed(str(exc))
    
    def _mock_verify(
        self,
        nin: str,
        first_name: str,
        last_name: str,
        dob: date,
    ) -> NIMCVerificationResult:
        """Mock verification for test/development."""
        return NIMCVerificationResult(
            nin=nin,
            first_name=first_name,
            last_name=last_name,
            middle_name="",
            date_of_birth=dob,
            gender="M",
            state="Lagos",
            lga="Alimosho",
            phone="08012345678",
            email=f"{first_name.lower()}@example.com",
            is_verified=True,
        )
    
    def _api_verify(
        self,
        nin: str,
        first_name: str,
        last_name: str,
        dob: date,
    ) -> NIMCVerificationResult:
        """Real NIMC API verification."""
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "nin": nin,
            "firstname": first_name,
            "lastname": last_name,
            " dob": dob.strftime("%Y-%m-%d"),
        }
        
        response = requests.post(
            f"{self.BASE_URL}/verify",
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        if response.status_code == 503:
            raise NIMCServiceUnavailable("NIMC service unavailable")
        
        if response.status_code != 200:
            raise NIMCVerificationFailed(
                f"Verification failed: {response.status_code}"
            )
        
        data = response.json()
        
        return NIMCVerificationResult(
            nin=nin,
            first_name=data.get("firstname", first_name),
            last_name=data.get("lastname", last_name),
            middle_name=data.get("middlename", ""),
            date_of_birth=dob,
            gender=data.get("gender", "M"),
            state=data.get("state", ""),
            lga=data.get("lga", ""),
            phone=data.get("phone"),
            email=data.get("email"),
        )


# Singleton
_nimc_client = None


def get_nimc_client() -> NIMCClient:
    """Get singleton NIMC client."""
    global _nimc_client
    if _nimc_client is None:
        _nimc_client = NIMCClient()
    return _nimc_client