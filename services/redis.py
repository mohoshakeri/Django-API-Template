import json
import uuid
from typing import Optional, Any, Generator

import redis
import zstandard as zstd
from cryptography.fernet import Fernet
from project_title.settings import REDIS_SERVER, SECRET_KEY

from CONSTANTS import DAY
from tools.datetimes import dt


class RedisClient:
    DEFAULT_EXPIRE: int = DAY
    client: redis.Redis
    cipher: Fernet
    COMPRESS_LEVEL: int = 3

    def __init__(self) -> None:
        self.client = redis.StrictRedis.from_url(REDIS_SERVER)
        self.cipher = Fernet(SECRET_KEY)
        self.compressor = zstd.ZstdCompressor(level=self.COMPRESS_LEVEL)
        self.decompressor = zstd.ZstdDecompressor()

    def _encode(self, raw: bytes) -> bytes:
        return self.cipher.encrypt(self.compressor.compress(raw))

    def _decode(self, blob: bytes) -> bytes:
        return self.decompressor.decompress(self.cipher.decrypt(blob))

    @staticmethod
    def _serializer(obj: Any) -> str:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (dt.datetime, dt.date)):
            return obj.isoformat()
        raise TypeError("Type {} not serializable".format(type(obj)))

    def set_string(self, key: str, value: str, expire: int = DEFAULT_EXPIRE) -> None:
        raw: bytes = value.encode("utf-8")
        blob: bytes = self._encode(raw)
        self.client.set(name=key, value=blob, ex=expire)

    def get_string(self, key: str) -> Optional[str]:
        blob: Optional[bytes] = self.client.get(key)
        if blob is None:
            return None
        raw: bytes = self._decode(blob)
        return raw.decode("utf-8")

    def set_json(self, key: str, value: Any, expire: int = DEFAULT_EXPIRE) -> None:
        raw: bytes = json.dumps(
            value, ensure_ascii=False, default=self._serializer
        ).encode("utf-8")
        blob: bytes = self._encode(raw)
        self.client.set(name=key, value=blob, ex=expire)

    def get_json(self, key: str) -> Optional[Any]:
        blob: Optional[bytes] = self.client.get(key)
        if blob is None:
            return None
        raw: bytes = self._decode(blob)
        return json.loads(raw.decode("utf-8"))

    def set_int(self, key: str, value: int, expire: int = DEFAULT_EXPIRE) -> None:
        raw: bytes = str(value).encode("utf-8")
        blob: bytes = self._encode(raw)
        self.client.set(name=key, value=blob, ex=expire)

    def get_int(self, key: str) -> Optional[int]:
        blob: Optional[bytes] = self.client.get(key)
        if blob is None:
            return None
        raw: bytes = self._decode(blob)
        return int(raw.decode("utf-8"))

    def delete(self, key: str) -> None:
        self.client.delete(key)

    def get_keys_by_prefix(self, prefix: str) -> Generator[bytes, None, None]:
        all_keys: set = set()
        cursor: int = 0

        while True:
            cursor, keys = self.client.scan(
                cursor=cursor, match="{}*".format(prefix), count=100
            )
            for key in keys:
                # Handle Redis scan duplicates
                if key in all_keys:
                    continue
                all_keys.add(key)
                yield key
            if cursor == 0:
                break


# Global Redis client instance
redis_client: RedisClient = RedisClient()
