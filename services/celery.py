import json
import os
from typing import Any

import celery.signals as celery_signals
from celery import Celery
from project_title.log import logger_set

logger = logger_set("services.celery")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_title.settings")

app: Celery = Celery("project_title")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_connection_retry_on_startup = True


def get_task_name(sender: Any, task: Any = None) -> str:
    if hasattr(sender, "name") and sender.name:
        return sender.name
    if task and hasattr(task, "name") and task.name:
        return task.name
    return str(sender)


@celery_signals.task_received.connect
def log_task_received(sender=None, request=None, **kw):
    if sender and request:
        logger.info(
            msg={
                "event": "task_received",
                "task_id": request.id if hasattr(request, "id") else None,
                "task_name": (
                    request.name if hasattr(request, "name") else get_task_name(sender)
                ),
            }
        )


@celery_signals.task_prerun.connect
def log_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    if sender and task_id:
        logger.info(
            msg={
                "event": "task_prerun",
                "task_id": task_id,
                "task_name": get_task_name(sender, task),
                "args": args,
                "kwargs": kwargs,
            }
        )


@celery_signals.task_prerun.connect
def save_task_name_prerun(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kw
):
    from django_celery_results.models import TaskResult

    if sender and task_id:

        # Create or update task result record
        task_result, created = TaskResult.objects.get_or_create(
            task_id=task_id,
            defaults={
                "task_name": get_task_name(sender, task),
                "task_args": json.dumps(args) if args else "[]",
                "task_kwargs": json.dumps(kwargs) if kwargs else "{}",
                "status": "STARTED",
                "content_type": "application/json",
                "content_encoding": "utf-8",
            },
        )

        if not created:
            task_result.status = "STARTED"
            task_result.save()


@celery_signals.task_postrun.connect
def log_task_postrun(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **kw
):
    if sender and task_id:
        logger.info(
            msg={
                "event": "task_postrun",
                "task_id": task_id,
                "task_name": get_task_name(sender, task),
                "result": retval,
            }
        )


@celery_signals.task_failure.connect
def log_task_failure(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **kw,
):
    if sender and task_id:
        logger.error(
            msg={
                "event": "task_failure",
                "task_id": task_id,
                "task_name": get_task_name(sender),
                "args": args,
                "kwargs": kwargs,
            },
            exc_info=einfo,
        )


@celery_signals.task_internal_error.connect
def log_task_internal_error(
    sender=None,
    task_id=None,
    args=None,
    kwargs=None,
    request=None,
    exception=None,
    traceback=None,
    einfo=None,
    **kw,
):
    if sender and task_id:
        logger.critical(
            msg={
                "event": "task_internal_error",
                "task_id": task_id,
                "task_name": get_task_name(sender),
            },
            exc_info=einfo,
        )
    else:
        logger.critical(
            msg={
                "event": "task_internal_error",
            },
            exc_info=einfo,
        )


@celery_signals.task_rejected.connect
def log_task_rejected(sender=None, message=None, exc=None, **kw):
    if sender:
        logger.error(
            msg={
                "event": "task_rejected",
                "task_name": get_task_name(sender),
                "message": str(message),
                "error": str(exc),
            }
        )


# Auto-discover tasks from installed Django apps
app.autodiscover_tasks()
