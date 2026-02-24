from typing import Optional

from author.decorators import with_author
from project_title.log import logger_set

from apps.authentication.models import User
from tools.converters import _
from utils.abstract import AdminRequestAbstract, AbstractModel
from utils.db import *

logger = logger_set("manager.model")

__all__ = [
    "AdminActionLog",
    "ChargeWalletRequest",
    "WalletHistory",
]


class AdminActionLog(AbstractModel):
    admin: User = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="action_logs",
        verbose_name=_("admin"),
    )

    string_details: Optional[str] = models.TextField(
        verbose_name=_("string details"),
        null=True,
        blank=True,
    )
    structured_details: Optional[str] = models.TextField(
        verbose_name=_("structured details"),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("admin action log")
        verbose_name_plural = _("admin action logs")

    def __str__(self) -> str:
        return "{} - {}".format(self.admin, self.string_details)


@with_author
class ChargeWalletRequest(AdminRequestAbstract):
    user: User = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="admin_charge_requests",
        verbose_name=_("user"),
    )

    amount: int = models.IntegerField(verbose_name=_("amount"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("charge wallet request")
        verbose_name_plural = _("charge wallet requests")

    def __str__(self) -> str:
        status: str = _("Successful") if self.is_successful else _("Failed")
        return "{} - {} - {}".format(self.user, self.amount, status)

    def request_handler(self) -> None:
        try:
            with db_transaction.atomic():
                self.backup = {"PrevAmount": str(self.user.wallet)}
                self.user.charge_wallet(
                    self.amount,
                    "{} : {}".format(_("admin charge - action id"), self.id),
                )
                self.is_successful = True
                self.response = _("Successful")
                self.save()
            logger.info(
                msg={
                    "message": "Wallet Charged By Admin",
                    "user": str(self.user),
                    "amount": self.amount,
                    "request_id": self.id,
                }
            )
        except Exception as e:
            self.response = str(e)
            self.save()
            logger.warning(
                msg={
                    "message": "Wallet Charge Failed",
                    "user": str(self.user),
                    "amount": self.amount,
                    "request_id": self.id,
                    "error": str(e),
                }
            )


class WalletHistory(AbstractModel):
    user: User = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="wallet_history",
        verbose_name=_("user"),
    )

    before: int = models.IntegerField(verbose_name=_("before charge"))
    charge: int = models.IntegerField(verbose_name=_("charge amount"))

    @property
    def after(self) -> int:
        return self.before + self.charge

    after.fget.short_description = _("after charge")

    description: Optional[str] = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("wallet history")
        verbose_name_plural = _("wallet histories")

    def __str__(self) -> str:
        return "{} - {}".format(self.user, self.description)
