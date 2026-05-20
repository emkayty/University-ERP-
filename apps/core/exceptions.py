"""
Custom exception handler for API responses.
Standardizes error format across all endpoints.
"""

import uuid
from typing import Any, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework.views import exception_handler


class APIError(Exception):
    """Custom API error with standardized format."""
    
    def __init__(
        self,
        message: str,
        code: str = "error",
        details: Optional[Any] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(message)


def custom_exception_handler(exc: Exception, context: dict) -> JsonResponse:
    """
    Custom exception handler for REST Framework.
    
    Returns standardized response format:
    {
        "success": false,
        "data": null,
        "pagination": null,
        "errors": {...},
        "request_id": "uuid"
    }
    """
    request_id = uuid.uuid4()
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        return JsonResponse(
            {
                "success": False,
                "data": None,
                "pagination": None,
                "errors": {
                    "code": "validation_error",
                    "message": "Validation failed.",
                    "details": exc.message_dict if hasattr(exc, "message_dict") else str(exc),
                },
                "request_id": str(request_id),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Handle DRF exceptions
    response = exception_handler(exc, context)
    
    if response is not None:
        # Extract errors from response
        errors = _extract_errors(response.data)
        
        return JsonResponse(
            {
                "success": False,
                "data": None,
                "pagination": None,
                "errors": {
                    "code": getattr(exc, "default_code", "error"),
                    "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                    "details": errors,
                },
                "request_id": str(request_id),
            },
            status=response.status_code,
        )
    
    # Handle custom API errors
    if isinstance(exc, APIError):
        return JsonResponse(
            {
                "success": False,
                "data": None,
                "pagination": None,
                "errors": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "request_id": str(request_id),
            },
            status=exc.status_code,
        )
    
    # Handle permission errors
    if isinstance(exc, PermissionDenied):
        return JsonResponse(
            {
                "success": False,
                "data": None,
                "pagination": None,
                "errors": {
                    "code": "permission_denied",
                    "message": "You do not have permission to perform this action.",
                },
                "request_id": str(request_id),
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    
    # Handle authentication errors
    if isinstance(exc, NotAuthenticated):
        return JsonResponse(
            {
                "success": False,
                "data": None,
                "pagination": None,
                "errors": {
                    "code": "not_authenticated",
                    "message": "Authentication credentials were not provided.",
                },
                "request_id": str(request_id),
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
    # Handle generic errors
    return JsonResponse(
        {
            "success": False,
            "data": None,
            "pagination": None,
            "errors": {
                "code": "internal_error",
                "message": "An internal error occurred.",
                "details": str(exc) if __import__("django").conf.settings.DEBUG else None,
            },
            "request_id": str(request_id),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_errors(data: Any) -> Any:
    """Extract errors from DRF response data."""
    if isinstance(data, dict):
        return {key: _extract_errors(value) for key, value in data.items()}
    elif isinstance(data, list) and data:
        return [_extract_errors(item) for item in data]
    return str(data)


# Import for _extract_errors
import django  # noqa: E402