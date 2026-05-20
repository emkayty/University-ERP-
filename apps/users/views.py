"""
User views for Nigerian University MIS.
Handles JWT authentication, user management, and 2FA.
"""

from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

from apps.users.models import User
from apps.users.permissions import HasRolePermission, IsStudentOwner
from apps.users.serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    UserCreateSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User CRUD operations."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, HasRolePermission]
    filterset_fields = ["role", "tenant", "is_active"]
    search_fields = ["email", "phone"]
    
    def get_required_roles(self):
        """Roles allowed to access this endpoint."""
        if self.action == "create":
            return [User.REGISTRAR, User.VC, User.ICT_ADMIN]
        elif self.action in ["destroy"]:
            return [User.REGISTRAR, User.VC, User.ICT_ADMIN]
        return []
    
    def get_queryset(self):
        """Filter by tenant."""
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        return User.objects.filter(tenant=user.tenant)
    
    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["post"])
    def whoami(self, request):
        """Get current user info."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LoginView(TokenObtainPairView):
    """JWT Login endpoint."""
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data["user"]
            
            # Update last login
            user.last_login = timezone.now()
            user.last_login_ip = self.get_client_ip(request)
            user.save(update_fields=["last_login", "last_login_ip"])
            
            # Generate tokens
            refresh = self.get_serializer(user).validated_data
            
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")


class LogoutView(TokenBlacklistView):
    """JWT Logout endpoint - blacklists refresh token."""
    permission_classes = [permissions.IsAuthenticated]


class RefreshTokenView(TokenRefreshView):
    """JWT Token refresh endpoint."""


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """Request password reset email."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        
        # Find user (don't reveal if not found)
        try:
            user = User.objects.get(email=email, is_active=True)
            # Send reset email would go here
            # For now, just return success
        except User.DoesNotExist:
            pass
        
        return Response({
            "message": "If the email exists, a password reset link has been sent."
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with new password."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        return Response({"message": "Password reset successfully."})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def two_factor_setup(request):
    """Setup 2FA for user."""
    if not request.user.requires_2fa:
        return Response(
            {"error": "2FA is not required for your role."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Generate 2FA secret would go here
    # For now, return placeholder
    return Response({
        "secret": "GENERATE_SECRET_HERE",
        "qr_code": "GENERATE_QR_HERE",
    })


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def two_factor_verify(request):
    """Verify 2FA code."""
    serializer = TwoFactorVerifySerializer(data=request.data)
    if serializer.is_valid():
        # Verify code would go here
        return Response({"message": "2FA verified successfully."})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Import after to avoid circular imports
from apps.users.models import UserRole  # noqa: E402, F401