"""
User serializers for Nigerian University MIS.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.users.models import User, UserRole, MANDATORY_2FA_ROLES


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    requires_2fa = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "role",
            "role_display",
            "tenant",
            "is_active",
            "is_verified",
            "two_factor_enabled",
            "requires_2fa",
            "created_at",
            "updated_at",
            "last_login",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_login"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "phone",
            "role",
            "tenant",
        ]
    
    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserRegistrationSerializer(serializers.Serializer):
    """Self-registration serializer for new users."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone = serializers.CharField(max_length=20, required=False)
    role = serializers.ChoiceField(choices=UserRole.choices)
    
    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        # Only certain roles can self-register
        allowed_roles = {UserRole.STUDENT, UserRole.ALUMNI}
        if data.get("role") not in allowed_roles:
            raise serializers.ValidationError({
                "role": f"Self-registration is not allowed for this role."
            })
        return data
    
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({
                "new_password_confirm": "New passwords do not match."
            })
        return data
    
    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """JWT login serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    tenant_id = serializers.UUIDField(required=False)
    
    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        # Check for 2FA requirement
        if user.requires_2fa and not user.two_factor_enabled:
            raise serializers.ValidationError({
                "detail": "2FA is required for this role.",
                "requires_2fa": True,
            })
        
        data["user"] = user
        return data


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup."""
    secret = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)
    
    def validate_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Code must be 6 digits.")
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for 2FA verification."""
    code = serializers.CharField(min_length=6, max_length=6)
    
    def validate_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Code must be 6 digits.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value, is_active=True).exists():
            # Don't reveal if email exists
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({
                "new_password_confirm": "Passwords do not match."
            })
        return data