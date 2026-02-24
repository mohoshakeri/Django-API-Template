from typing import Any, Optional

from django.http import JsonResponse
from rest_framework.views import APIView


class HTTPError(Exception):
    def __init__(self, message: Optional[str] = None, status_code: int = 400, data: Optional[dict] = None):
        if data is None:
            data = {}
        if message:
            data["message"] = message
        self.status_code = status_code
        self.data = data


def get_object_or_error(status_code: int, message: Optional[str], klass: Any, *args: Any, **kwargs: Any) -> Any:
    if hasattr(klass, "_default_manager"):
        queryset = klass._default_manager.all()
    else:
        queryset = klass

    if message is None:
        message = "Object not found [404]"

    if not hasattr(queryset, "get"):
        klass__name: str = (
            klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        )
        raise ValueError(
            "First argument to get_object_or_error() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        raise HTTPError(message=message, status_code=status_code)


class BaseView(APIView):
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            response = super().dispatch(request, *args, **kwargs)
            return response
        except HTTPError as exc:
            return JsonResponse(data=exc.data, status=exc.status_code)
