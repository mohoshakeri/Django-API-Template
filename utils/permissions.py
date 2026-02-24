from typing import Optional, Tuple, List

from project_title.settings import SECRET_KEY
from rest_framework import permissions, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException

from apps.authentication.models import User
from tools.security import decode_token
from utils.session import Session


class ArgsPermission(permissions.BasePermission):
    def __call__(self):
        return self


class AuthenticationError(APIException):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    default_detail: str = "Authentication Error"
    default_code: str = "access_denied"


class AccessError(APIException):
    status_code: int = status.HTTP_403_FORBIDDEN
    default_detail: str = "Access Denied"
    default_code: str = "access_denied"


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.user and request.user.is_authenticated:
            return True
        raise AuthenticationError("Authentication Error!")


class FeaturePermission(ArgsPermission):
    def __init__(self, *features: str) -> None:
        self.features: Tuple[str, ...] = features

    def has_permission(self, request, view) -> bool:
        if all(
            [
                request.user.is_authenticated and f in request.user.feature_perms
                for f in self.features
            ]
        ):
            return True
        raise AccessError("You are not allowed to access this feature!")


class OrPermission(ArgsPermission):
    def __init__(self, *perms) -> None:
        self.perms: List = [p() if isinstance(p, type) else p for p in perms]

    def has_permission(self, request, view) -> bool:
        errors: List[APIException] = []
        for perm in self.perms:
            try:
                if perm.has_permission(request, view):
                    return True
            except APIException as exc:
                errors.append(exc)

        if errors:
            raise errors[0]
        return False


class TemporaryLinkAuthentication(BaseAuthentication):
    def authenticate(self, request) -> Optional[Tuple[User, None]]:
        token: Optional[str] = request.GET.get("AccessToken")
        if not token:
            return None

        # Validate Token
        data: Optional[dict] = decode_token(key=SECRET_KEY, token=token)
        if not data or "user_id" not in data:
            raise AuthenticationError("Invalid Token")

        user_id: int = data["user_id"]

        # Authenticate User
        user: Optional[User] = User.objects.filter(pk=user_id).first()
        if not user:
            raise AuthenticationError("Invalid User Token")
        if not user.is_active:
            raise AuthenticationError("User is not Active")

        request.user = user
        request.session = None

        return user, None


class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request) -> Optional[Tuple[User, str]]:
        token: Optional[str] = request.META.get("HTTP_AUTHORIZATION")
        if not (token and token.startswith("Bearer ")):
            return None

        token = token[7:]  # Remove "Bearer " Prefix

        # Validate Session
        session: Optional[Session] = Session(token=token).initialize()
        if not (session and session.is_accessable):
            raise AuthenticationError("Invalid Token")

        # Authenticate User
        user: Optional[User] = session.get_user()
        if not user:
            raise AuthenticationError("Invalid User Token")
        if not user.is_active:
            raise AuthenticationError("User is not Active")

        request.user = user
        request.session = session

        # Auto-Refresh Session Expiration
        session.refresh()
        return user, session.token
