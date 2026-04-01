from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.constants import LOCKOUT_WINDOW_MINUTES, MAX_LOGIN_ATTEMPTS
from core.ip_utils import get_client_ip
from core.audit import log_audit
from findings.models import AuditLog

from .models import LoginAttempt, PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from core.throttles import LoginThrottle, PasswordResetThrottle, RegistrationThrottle

User = get_user_model()

LOCKOUT_WINDOW = timedelta(minutes=LOCKOUT_WINDOW_MINUTES)


def _is_locked_out(ip, username=None):
    """Return True if the IP or account has exceeded the failure threshold."""
    cutoff = timezone.now() - LOCKOUT_WINDOW

    if ip:
        ip_failures = LoginAttempt.objects.filter(
            ip_address=ip, success=False, created_at__gte=cutoff
        ).count()
        if ip_failures >= MAX_LOGIN_ATTEMPTS:
            return True

    if username:
        account_failures = LoginAttempt.objects.filter(
            username=username, success=False, created_at__gte=cutoff
        ).count()
        if account_failures >= MAX_LOGIN_ATTEMPTS:
            return True

    return False


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def register(request):
    """Create a new user account and return an authentication token."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    log_audit(
        request, AuditLog.Action.REGISTER, "user", user.pk,
        metadata={"username": user.username},
    )
    return Response(
        {"user": UserSerializer(user).data, "token": token.key},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    """Authenticate with username and password, returning a token on success."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    ip = get_client_ip(request)

    if _is_locked_out(ip, username):
        return Response(
            {"error": "Too many failed login attempts. Try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    user = authenticate(
        username=username,
        password=serializer.validated_data["password"],
    )
    if not user:
        LoginAttempt.objects.create(username=username, ip_address=ip, success=False)
        log_audit(
            request, AuditLog.Action.LOGIN_FAILED, "user",
            metadata={"username": username},
        )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    LoginAttempt.objects.create(username=username, ip_address=ip, success=True)
    token, _ = Token.objects.get_or_create(user=user)
    log_audit(
        request, AuditLog.Action.LOGIN, "user", user.pk,
        metadata={"username": user.username},
    )
    return Response({"user": UserSerializer(user).data, "token": token.key})


@api_view(["POST"])
def logout(request):
    """Invalidate the current authentication token."""
    log_audit(
        request, AuditLog.Action.LOGOUT, "user", request.user.pk,
        metadata={"username": request.user.username},
    )
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "PATCH"])
def me(request):
    """Return or update the profile of the currently authenticated user."""
    if request.method == "GET":
        return Response(UserSerializer(request.user).data)

    serializer = ProfileUpdateSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)

    user = request.user
    data = serializer.validated_data
    updated_fields = []

    if "email" in data:
        user.email = data["email"]
        updated_fields.append("email")
    if "first_name" in data:
        user.first_name = data["first_name"]
        updated_fields.append("first_name")
    if "last_name" in data:
        user.last_name = data["last_name"]
        updated_fields.append("last_name")

    if updated_fields:
        user.save(update_fields=updated_fields)
        log_audit(
            request, AuditLog.Action.PROFILE_UPDATE, "user", user.pk,
            metadata={"updated_fields": updated_fields},
        )

    return Response(UserSerializer(user).data)


@api_view(["POST"])
def change_password(request):
    """Change the authenticated user's password. Invalidates other tokens."""
    serializer = ChangePasswordSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)

    user = request.user
    # nosemgrep: python.django.security.audit.unvalidated-password.unvalidated-password — validated in ChangePasswordSerializer.validate_new_password()
    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password"])

    Token.objects.filter(user=user).exclude(key=request.auth.key).delete()

    log_audit(
        request, AuditLog.Action.PASSWORD_CHANGE, "user", user.pk,
        metadata={"username": user.username},
    )

    return Response({"message": "Password changed successfully."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def forgot_password(request):
    """Request a password reset token. Always returns 200."""
    email = request.data.get("email", "").strip()
    if not email:
        return Response(
            {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email__iexact=email)
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
            used_at=timezone.now()
        )
        reset_token = PasswordResetToken.objects.create(user=user)
        log_audit(
            request, AuditLog.Action.PASSWORD_RESET_REQUEST, "user", user.pk,
            metadata={"email": email},
        )

        try:
            from core.emails import send_password_reset_email
            send_password_reset_email(user, reset_token.token)
        except (OSError, ConnectionError, RuntimeError):
            pass  # Swallow send failures — never leak account existence
    except User.DoesNotExist:
        pass

    return Response({"message": "If an account with that email exists, a reset link has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def reset_password(request):
    """Reset password using a valid token. Invalidates all existing auth sessions."""
    token_str = request.data.get("token", "")
    new_password = request.data.get("password", None)

    if not token_str or not new_password:
        return Response(
            {"error": "Token and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        reset_token = PasswordResetToken.objects.select_related("user").get(token=token_str)
    except PasswordResetToken.DoesNotExist:
        return Response(
            {"error": "Invalid or expired reset token."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not reset_token.is_valid():
        return Response(
            {"error": "Invalid or expired reset token."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    try:
        validate_password(new_password, user=reset_token.user)
    except ValidationError as e:
        return Response(
            {"error": e.messages}, status=status.HTTP_400_BAD_REQUEST
        )

    user = reset_token.user
    user.set_password(new_password)
    user.save(update_fields=["password"])

    reset_token.used_at = timezone.now()
    reset_token.save(update_fields=["used_at"])

    Token.objects.filter(user=user).delete()

    log_audit(
        request, AuditLog.Action.PASSWORD_RESET_COMPLETE, "user", user.pk,
        metadata={"username": user.username},
    )

    return Response({"message": "Password has been reset successfully. Please log in again."})
