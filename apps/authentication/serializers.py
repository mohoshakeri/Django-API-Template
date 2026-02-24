from functools import partial
from random import randint
from typing import Tuple, Optional

from project_title.log import logger_set
from project_title.settings import (
    ADMIN_LOGIN_MOBILE,
    SECRET_KEY,
)
from rest_framework import serializers

from CONSTANTS import (
    VERIFICATION_CODE_CACHE_PREFIX,
    VERIFICATION_CODE_CACHE_AGE,
    UNSUCCESSFUL_LOGIN_COUNT_CACHE_PREFIX,
    MAX_UNSUCCESSFUL_LOGIN_COUNT,
    UNSUCCESSFUL_LOGIN_COUNT_CACHE_AGE,
)
from services.redis import redis_client
from services.sms import SMS
from tools.security import create_token
from utils.db import db_transaction
from utils.session import Session
from utils.validators import *
from .models import *

logger = logger_set("authentication.serializer")

__all__ = [
    "AuthenticationSerializer",
    "UserSerializer",
    "SetPasswordSerializer",
]


class AuthenticationSerializer(serializers.Serializer):
    mobile: str = serializers.CharField(validators=[MobileValidtor()])
    verification_code: str = serializers.CharField(
        validators=[RegexValidator(r"^\d{5}$", "Must be 5 digits")],
        required=False,
    )
    password: str = serializers.CharField(required=False)

    def send_code(self, as_admin: bool = False) -> None:
        mobile: str = self.validated_data["mobile"]
        code: int = randint(11111, 99999)
        code = 12345  # Todo -> Delete

        sms: SMS = SMS("VCode").ready(code=str(code))
        if as_admin:
            send_func = partial(sms.send, mobile=ADMIN_LOGIN_MOBILE)
        else:
            send_func = partial(sms.send, mobile=mobile)

        # Cache And Send Verification Code
        cache_key: str = VERIFICATION_CODE_CACHE_PREFIX + mobile
        redis_client.set_string(cache_key, str(code), VERIFICATION_CODE_CACHE_AGE)
        send_func()

        logger.info(
            msg={"message": "Verification Code", "code": code, "mobile": mobile}
        )

    def is_active(self) -> bool:
        mobile: str = self.validated_data["mobile"]
        user: Optional[User] = User.objects.filter(mobile=mobile).first()
        return not user or user.is_active

    def has_password(self) -> bool:
        mobile: str = self.validated_data["mobile"]
        user: Optional[User] = User.objects.filter(mobile=mobile).first()
        return bool(user and user.has_usable_password())

    def auth_by_password(self) -> Tuple[str | None, User | None]:
        mobile: str = self.validated_data["mobile"]
        user: Optional[User] = User.objects.filter(mobile=mobile).first()

        if not (
            user and user.has_usable_password() and "password" in self.validated_data
        ):
            return None, None

        raw_password = self.validated_data["password"]
        if user.check_password(raw_password):
            return self.login(user), user
        return None, None

    def verify(self) -> bool:
        mobile: str = self.validated_data["mobile"]
        code: Optional[str] = self.validated_data.get("verification_code")
        if not code:
            return False

        cache_key: str = VERIFICATION_CODE_CACHE_PREFIX + mobile
        vcode_cache: Optional[str] = redis_client.get_string(cache_key)

        result: bool = vcode_cache is not None and vcode_cache == code
        if result:
            redis_client.delete(cache_key)
        return result

    def login_or_register(self) -> Tuple[str, User, bool]:
        mobile: str = self.validated_data["mobile"]
        user: Optional[User] = User.objects.filter(mobile=mobile).first()

        if user:
            return self.login(user), user, False

        # Register New User
        user = self.register(mobile)
        return self.login(user), user, True

    def login(self, user: User) -> str:
        session: Session = Session(user_id=user.pk).create()
        return session.token

    def register(self, mobile: str) -> User:
        with db_transaction.atomic():
            user: User = User.objects.create_user(mobile=mobile)
            user.initial_action()
            return user

    def create_password_perm_token(self, user: User) -> str:
        return create_token(
            key=SECRET_KEY, data={"user_id": user.pk}, expire_minutes=15
        )

    @staticmethod
    def set_password(password: str, user: User) -> None:
        user.set_password(password)
        user.save()

    def add_and_check_unsuccessful_login_limit(self) -> None:
        # Get Cache
        mobile: str = self.validated_data["mobile"]
        cache_key: str = UNSUCCESSFUL_LOGIN_COUNT_CACHE_PREFIX + mobile
        count: Optional[int] = redis_client.get_int(cache_key)
        if count is None:
            count = 0

        # Add Count
        count += 1

        if count >= MAX_UNSUCCESSFUL_LOGIN_COUNT:
            user: Optional[User] = User.objects.filter(mobile=mobile).first()

            if user:
                user.is_active = False
                user.save()
                self.reset_unsuccessful_login_limit()
        else:
            redis_client.set_int(cache_key, count, UNSUCCESSFUL_LOGIN_COUNT_CACHE_AGE)

    def reset_unsuccessful_login_limit(self) -> None:
        mobile: str = self.validated_data["mobile"]
        cache_key: str = UNSUCCESSFUL_LOGIN_COUNT_CACHE_PREFIX + mobile
        redis_client.delete(cache_key)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "mobile",
            "name",
            "address",
            "wallet",
            "created_at",
        ]
        read_only_fields = [
            "mobile",
            "wallet",
            "created_at",
        ]


class SetPasswordSerializer(serializers.Serializer):
    password: str = serializers.RegexField(
        regex=r"^(?=.*[A-Za-z])(?=.*\d).{8,}$",
        error_messages={
            "invalid": "رمز عبور باید حداقل ۸ کاراکتر و شامل حرف و عدد باشد."
        },
    )
