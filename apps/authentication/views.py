from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from project_title.log import logger_set
from utils.db import db_transaction
from utils.permissions import IsAuthenticated, TemporaryLinkAuthentication
from utils.views import BaseView
from .serializers import *

logger = logger_set("authentication.view")

__all__ = [
    "Authentication",
    "Password",
]


class Authentication(BaseView):
    """
    GET -> Get Information | Send Verification Code
    POST -> Login Or Register
    PUT -> Update User Information
    DELETE -> Logout
    """

    class VerificationCodeThrottle(AnonRateThrottle):
        scope = "vcode"

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_throttles(self):
        if self.request.method == "GET" and not (
            self.request.user and self.request.user.is_authenticated
        ):
            return [self.VerificationCodeThrottle()]
        return super().get_throttles()

    def get(self, request, **kwargs):
        # Send User Info
        if request.user and request.user.is_authenticated:
            ser = UserSerializer(instance=request.user)
            return Response(ser.data)

        # Send Verification Code For Auth
        ser = AuthenticationSerializer(data=request.GET)
        if not ser.is_valid():
            return Response({"devMessages": ser.errors}, status.HTTP_400_BAD_REQUEST)

        if not ser.is_active():
            return Response(
                {"message": "اکانت شما غیرفعال است. با پشتیبانی تماس بگیرید."},
                status.HTTP_400_BAD_REQUEST,
            )

        ser.send_code(as_admin=request.GET.get("as_admin") == "1")
        return Response({"has_password": ser.has_password()})

    def post(self, request, **kwargs):
        ser = AuthenticationSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"devMessages": ser.errors}, status.HTTP_400_BAD_REQUEST)

        if not ser.is_active():
            return Response(
                {"message": "اکانت شما غیرفعال است. با پشتیبانی تماس بگیرید."},
                status.HTTP_400_BAD_REQUEST,
            )

        # Password Auth
        password_auth_token, user = ser.auth_by_password()
        if password_auth_token:
            ser.reset_unsuccessful_login_limit()
            logger.info(
                msg={
                    "message": "User Login",
                    "mobile": user.mobile,
                    "method": "password",
                }
            )
            return Response(
                {
                    "token": password_auth_token,
                    "new_user": not user.name,
                    "password_perm_token": None,
                }
            )

        # Code Auth
        if ser.verify():
            token, user, created = ser.login_or_register()
            ser.reset_unsuccessful_login_limit()
            logger.info(
                msg={
                    "message": "User Register" if created else "User Login",
                    "mobile": user.mobile,
                    "method": "code",
                }
            )
            return Response(
                {
                    "token": token,
                    "new_user": created or not user.name,
                    "password_perm_token": (
                        ser.create_password_perm_token(user) if created else None
                    ),
                }
            )

        # Failed Attempt
        ser.add_and_check_unsuccessful_login_limit()
        logger.warning(
            msg={
                "message": "Failed Login Attempt",
                "mobile": ser.validated_data["mobile"],
            }
        )
        return Response(
            {"message": "اطلاعات ورود نامعتبر است."}, status.HTTP_400_BAD_REQUEST
        )

    def put(self, request, **kwargs):
        ser = UserSerializer(instance=request.user, data=request.data, many=False)
        if not ser.is_valid():
            return Response({"devMessages": ser.errors}, status.HTTP_400_BAD_REQUEST)

        ser.save()
        logger.info(msg={"message": "User Info Updated", "mobile": request.user.mobile})
        return Response({})

    def delete(self, request, **kwargs):
        logger.info(msg={"message": "User Logout", "mobile": request.user.mobile})
        request.session.flush()
        return Response({})


class Password(BaseView):
    """
    GET -> Send Verification Code [Login Permission]
    POST -> Authorization and get Permission [Login Permission]
    PUT -> Set Password [JWT Permission]
    DELETE -> Disable Password [Login Permission]
    """

    permission_classes = [IsAuthenticated]

    class VerificationCodeThrottle(AnonRateThrottle):
        scope = "vcode"

    def get_authenticators(self):
        if self.request.method == "PUT":
            return [TemporaryLinkAuthentication()]
        return super().get_authenticators()

    def get_throttles(self):
        if self.request.method == "GET":
            return [self.VerificationCodeThrottle()]
        return super().get_throttles()

    def get(self, request, **kwargs):
        # Send Verification Code For Auth
        ser = AuthenticationSerializer(data={"mobile": request.user.mobile})
        if not ser.is_valid():
            return Response({"devMessages": ser.errors}, status.HTTP_400_BAD_REQUEST)

        ser.send_code()
        return Response({})

    def post(self, request, **kwargs):
        ser = AuthenticationSerializer(
            data={**request.data, "mobile": request.user.mobile}
        )
        if not ser.is_valid():
            return Response({"devMessages": ser.errors}, status.HTTP_400_BAD_REQUEST)

        if not ser.verify():
            return Response(
                {"message": "کد تایید نامعتبر است."}, status.HTTP_400_BAD_REQUEST
            )

        token: str = ser.create_password_perm_token(request.user)
        logger.info(
            msg={
                "message": "Password Permission Granted",
                "mobile": request.user.mobile,
            }
        )
        return Response({"perm_token": token})

    def put(self, request, **kwargs):
        ser = SetPasswordSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"devMessages": ser.errors}, status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            AuthenticationSerializer.set_password(
                ser.validated_data["password"], request.user
            )
        logger.info(msg={"message": "Password Changed", "mobile": request.user.mobile})
        return Response({})

    def delete(self, request, **kwargs):
        request.user.set_unusable_password()
        request.user.save()
        logger.info(msg={"message": "Password Disabled", "mobile": request.user.mobile})
        return Response({})
