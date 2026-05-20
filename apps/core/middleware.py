"""
Middleware for Nigerian University MIS.
Includes audit logging, tenant resolution, and security headers.
"""

import time
import uuid
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from apps.core.models import AuditLog


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log every API request to AuditLog model.
    
    Records:
    - User (if authenticated)
    - Tenant (from connection.schema_name)
    - IP address
    - User agent
    - Method, path, query string
    - Status code
    - Duration in milliseconds
    
    IMPORTANT: This middleware should be applied early in MIDDLEWARE.
    """
    
    # Paths to exclude from audit logging
    EXCLUDED_PATHS = ["/health/", "/metrics/", "/__health__/"]
    
    def process_request(self, request: HttpRequest) -> None:
        """Store start time for duration calculation."""
        request._audit_start_time = time.time()
        request._audit_request_id = uuid.uuid4()
    
    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        """Log the request details."""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response
        
        # Skip non-API paths
        if not request.path.startswith("/api/"):
            return response
        
        # Calculate duration
        duration_ms = int((time.time() - getattr(request, "_audit_start_time", time.time())) * 1000)
        
        # Get user and tenant
        user = getattr(request, "user", None)
        tenant = getattr(request, "tenant", None)
        
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Create audit log (async in production would be better)
        try:
            AuditLog.objects.create(
                user=user if user and user.is_authenticated else None,
                tenant=tenant,
                ip_address=ip_address,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                method=request.method,
                path=request.path,
                query_string=request.META.get("QUERY_STRING", ""),
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=getattr(request, "_audit_request_id", None),
            )
        except Exception:
            # Don't let audit logging break requests
            pass
        
        return response
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")


class TenantResolutionMiddleware(MiddlewareMixin):
    """
    Middleware to resolve tenant from request.
    
    Resolution order:
    1. X-Tenant-ID header
    2. Subdomain from domain
    3. JWT token tenant claim
    
    Sets:
    - request.tenant
    - connection.schema_name (for django-tenants)
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Resolve tenant for the request."""
        from django_tenants.utils import get_tenant
        
        tenant = None
        
        # 1. Try X-Tenant-ID header
        tenant_id = request.META.get("HTTP_X_TENANT_ID")
        if tenant_id:
            try:
                from apps.tenants.models import University
                tenant = University.objects.get(slug=tenant_id, is_active=True)
            except University.DoesNotExist:
                pass
        
        # 2. Try subdomain
        if not tenant:
            host = request.get_host().split(":")[0]
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api", "localhost"]:
                    try:
                        from apps.tenants.models import University
                        tenant = University.objects.get(slug=subdomain, is_active=True)
                    except University.DoesNotExist:
                        pass
        
        # 3. Try JWT tenant claim
        if not tenant and hasattr(request, "user") and request.user.is_authenticated:
            tenant = getattr(request.user, "tenant", None)
        
        # Set on request
        request.tenant = tenant
        
        # Set for django-tenants
        if tenant:
            try:
                from django.db import connection
                connection.set_tenant(tenant)
            except Exception:
                pass
    
    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        """Reset tenant after request."""
        try:
            from django.db import connection
            connection.set_schema_to_public()
        except Exception:
            pass
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: various restrictions
    
    Only applied in production.
    """
    
    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        """Add security headers."""
        # Skip in development
        if getattr(settings, "DEBUG", False):
            return response
        
        # Add headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Add CSP header
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        
        return response


class TenantAdminMiddleware(MiddlewareMixin):
    """
    Middleware to add tenant ID to admin interface.
    
    Required to show tenant-specific content in Django Admin.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Set tenant for admin."""
        if request.path.startswith("/admin/") and hasattr(request, "user"):
            if request.user.is_authenticated and hasattr(request.user, "tenant"):
                request.tenant = request.user.tenant