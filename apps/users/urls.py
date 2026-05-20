"""
User URLs for Nigerian University MIS.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users import views

urlpatterns = [
    # JWT Authentication
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("refresh/", views.RefreshTokenView.as_view(), name="token_refresh"),
    
    # Password Management
    path("password/reset/", views.password_reset_request, name="password_reset_request"),
    path("password/reset/confirm/", views.password_reset_confirm, name="password_reset_confirm"),
    
    # Two-Factor Authentication
    path("2fa/setup/", views.two_factor_setup, name="two_factor_setup"),
    path("2fa/verify/", views.two_factor_verify, name="two_factor_verify"),
    
    # User endpoints
    path("me/", views.UserViewSet.as_view({"get": "whoami", "patch": "partial_update"}), name="user_me"),
    path("change-password/", views.UserViewSet.as_view({"post": "change_password"}), name="change_password"),
]