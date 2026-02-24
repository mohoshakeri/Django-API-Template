from typing import Any, Optional

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from project_title.log import logger_set

from tools.converters import add_YE_to_persian_name, _
from utils.abstract import AbstractModel
from utils.db import *
from utils.validators import *

logger = logger_set("authentication.model")

__all__ = [
    "User",
]


class _UserManager(BaseUserManager):
    def create_user(
        self, mobile: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        if not mobile:
            raise ValueError("Mobile Is Required")

        user = self.model(mobile=mobile, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # Disable Password Login

        user.save(using=self._db)
        return user

    def create_superuser(
        self, mobile: str, password: str, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(mobile, password, **extra_fields)


class User(AbstractModel, AbstractBaseUser, PermissionsMixin):
    mobile: str = models.CharField(
        verbose_name=_("mobile"),
        max_length=11,
        unique=True,
        validators=[MobileValidtor()],
    )

    is_active: bool = models.BooleanField(verbose_name=_("active"), default=True)
    is_staff: bool = models.BooleanField(verbose_name=_("staff"), default=False)

    name: Optional[str] = models.CharField(
        verbose_name=_("name"),
        max_length=150,
        validators=[FullPersianLetterValidator()],
        null=True,
        blank=True,
    )
    address: Optional[str] = models.TextField(
        verbose_name=_("address"), null=True, blank=True
    )

    wallet: int = models.IntegerField(verbose_name=_("wallet"), default=0)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    objects = _UserManager()

    USERNAME_FIELD = "mobile"

    def __str__(self) -> str:
        return self.mobile

    @property
    def dialog_name(self) -> str:
        name: str = self.name
        return add_YE_to_persian_name(name)

    def initial_action(self) -> None:
        pass

    def charge_wallet(self, value: int, description: Optional[str] = None) -> None:
        user_locked: User = User.objects.select_for_update().get(id=self.id)
        self.wallet_history.create(
            before=user_locked.wallet,
            charge=value,
            description=description,
        )
        user_locked.wallet += value
        user_locked.save()
        return
