from typing import Optional

from django.db import models

from tools.converters import _
from tools.datetimes import dt


class AbstractModel(models.Model):
    id: int = models.AutoField(primary_key=True)
    created_at: dt.datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at: dt.datetime = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )

    class Meta:
        abstract = True


class AdminRequestAbstract(AbstractModel):
    is_successful: bool = models.BooleanField(
        verbose_name=_("successful"),
        default=False,
    )
    description: Optional[str] = models.TextField(
        verbose_name=_("description"),
        null=True,
        blank=True,
    )
    response: Optional[str] = models.TextField(
        verbose_name=_("response"),
        null=True,
        blank=True,
    )
    docs: Optional[str] = models.FileField(
        verbose_name=_("documents"),
        upload_to="admin/documents/",
        null=True,
        blank=True,
    )
    backup: dict = models.JSONField(
        verbose_name=_("backup"),
        default=dict,
        blank=True,
    )

    class Meta:
        abstract = True

    def request_handler(self) -> None:
        pass

    def save(self, **kwargs) -> None:
        if not self.id:
            super().save(**kwargs)
            self.request_handler()
        else:
            super().save(**kwargs)
