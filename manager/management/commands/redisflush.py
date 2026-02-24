from typing import Any

import redis
from django.core.management.base import BaseCommand, CommandParser
from project_title.settings import REDIS_SERVER


class Command(BaseCommand):
    help = "Flush Redis Cache"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-p",
            "--prefix",
            default=None,
            type=str,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        prefix: str = options["prefix"]

        redis_client: redis.StrictRedis = redis.StrictRedis.from_url(REDIS_SERVER)

        if prefix:
            keys_to_delete: list = []
            cursor: int = 0

            while True:
                cursor, keys = redis_client.scan(
                    cursor=cursor, match="{}*".format(prefix), count=100
                )
                for key in keys:
                    keys_to_delete.append(key)
                if len(keys_to_delete) >= 100:
                    redis_client.delete(*keys_to_delete)
                    keys_to_delete = []
                if cursor == 0:
                    break

            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
        else:
            redis_client.flushall()

        self.stdout.write(self.style.SUCCESS("Redis Flushed"))
