import json
import os
import time

from django.db import connection
from django.http import Http404, HttpResponseForbidden, FileResponse
from django.utils.deprecation import MiddlewareMixin
from project_title import settings
from project_title.log import logger_set
from project_title.settings import MEDIA_URL

logger = logger_set("utils.middlewares")


class IPIdentificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        remote_addr = request.META.get("REMOTE_ADDR")
        ip = remote_addr

        # Check proxy server (if exists)
        if remote_addr == "127.0.0.1":
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0].strip()
            else:
                x_real_ip = request.META.get("HTTP_X_REAL_IP")
                if x_real_ip:
                    ip = x_real_ip.strip()

        request.ip = ip


class IPBlockMiddleware(MiddlewareMixin):
    def process_request(self, request):
        from django.conf import settings

        blocked_ips = getattr(settings, "IP_BLOCKEDS", [])

        # Check If IP Is Blocked
        if hasattr(request, "ip") and request.ip in blocked_ips:
            return HttpResponseForbidden("Access Denied")
        return None


class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

        # Parse Body
        body = request.body
        if isinstance(body, bytes):
            try:
                body = body.decode("utf-8")
                try:
                    body = json.loads(body)
                except json.decoder.JSONDecodeError:
                    pass
            except UnicodeDecodeError:
                body = ""

        request._parsed_body = body

    def process_response(self, request, response):
        duration = time.time() - request._start_time

        # Set Level
        if response.status_code >= 500:
            log_method = logger.error
        elif response.status_code == 404:
            log_method = logger.warning
        elif response.status_code >= 400:
            log_method = logger.info
        else:
            log_method = logger.info

        log_method(
            {
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "ip": request.ip,
                "body": request._parsed_body,
                "files": len(request.FILES),
                "query_params": dict(request.GET),
                "user": (
                    getattr(request.user, "id", None)
                    if hasattr(request, "user")
                    else None
                ),
                "db_request_count": len(connection.queries),
            }
        )

        return response

    def process_exception(self, request, exception):
        logger.error(
            {
                "method": request.method,
                "path": request.path,
                "status_code": 500,
                "duration_ms": None,
                "ip": request.ip,
                "body": request._parsed_body,
                "files": len(request.FILES),
                "query_params": dict(request.GET),
                "user": (
                    getattr(request.user, "id", None)
                    if hasattr(request, "user")
                    else None
                ),
                "db_request_count": len(connection.queries),
            },
            exc_info=True,
        )

        return None


class MediaMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith(MEDIA_URL):
            # Check Private Access
            if request.path.startswith("{}admin/".format(MEDIA_URL)):
                user = request.user
                if not user.is_authenticated or not (
                    user.is_staff or user.is_superuser
                ):
                    raise Http404

            # Serve Files
            file_path = os.path.join(
                settings.MEDIA_ROOT, request.path[len(MEDIA_URL) :]
            )
            if not os.path.exists(file_path):
                raise Http404

            return FileResponse(open(file_path, "rb"))

        return None
