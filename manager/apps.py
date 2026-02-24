from django.apps import AppConfig

from tools.converters import _


class ManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "manager"
    label = "manager"
    verbose_name = _("manager")
