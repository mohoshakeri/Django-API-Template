import secrets
from typing import Optional, Generator

from django.core.exceptions import ObjectDoesNotExist
from pydantic import BaseModel, Field, PrivateAttr

from CONSTANTS import (
    USER_SESSION_KEY_PREFIX,
    USER_SESSION_FULL_AGE,
    USER_SESSION_RENEWAL_AGE,
)
from apps.authentication.models import User
from services.redis import redis_client
from tools.datetimes import dt

SESSION_FULL_AGE: int = USER_SESSION_FULL_AGE
SESSION_RENEWAL_AGE: int = USER_SESSION_RENEWAL_AGE


class ConflictTokenError(Exception):
    pass


class Session(BaseModel):
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    user_id: Optional[int] = Field(default=None)
    content: dict = Field(default_factory=dict)
    expired: float = Field(
        default_factory=lambda: (
            dt.datetime.now() + dt.timedelta(seconds=SESSION_FULL_AGE)
        ).timestamp()
    )
    _user_obj: Optional[User] = PrivateAttr(default=None)

    @property
    def full_token(self) -> str:
        return USER_SESSION_KEY_PREFIX + self.token

    def initialize(self) -> Optional["Session"]:
        session: Optional[dict] = redis_client.get_json(self.full_token)
        if session:
            self.user_id = session["user_id"]
            self.content = session["content"]
            self.expired = session["expired"]
            return self
        return None

    def create(self) -> "Session":
        created: Optional[Session] = self.initialize()
        if not created:
            redis_client.set_json(
                key=self.full_token, value=self.model_dump(), expire=SESSION_RENEWAL_AGE
            )
            return self
        raise ConflictTokenError("TOKEN: {}".format(self.token))

    @property
    def is_accessable(self) -> bool:
        return bool(self.user_id and self.expired > dt.datetime.now().timestamp())

    def get_user(self) -> Optional[User]:
        try:
            user: User = User.objects.get(id=self.user_id)
            self._user_obj = user
            return user
        except ObjectDoesNotExist:
            return None

    def update(self) -> "Session":
        redis_client.set_json(
            key=self.full_token, value=self.model_dump(), expire=SESSION_RENEWAL_AGE
        )
        return self

    def clear(self) -> "Session":
        self.content = {}
        redis_client.set_json(
            key=self.full_token, value=self.model_dump(), expire=SESSION_RENEWAL_AGE
        )
        return self

    def refresh(self) -> "Session":
        redis_client.set_json(
            key=self.full_token, value=self.model_dump(), expire=SESSION_RENEWAL_AGE
        )
        return self

    def flush(self) -> None:
        redis_client.delete(key=self.full_token)


def get_all_sessions() -> Generator[Session, None, None]:
    redis_keys: Generator = redis_client.get_keys_by_prefix(
        prefix=USER_SESSION_KEY_PREFIX
    )

    for key in redis_keys:
        session_token: str = key.decode("utf-8")[len(USER_SESSION_KEY_PREFIX):]
        session: Session = Session(token=session_token)
        yield session


def get_healthy_sessions() -> Generator[Session, None, None]:
    for s in get_all_sessions():
        session: Optional[Session] = s.initialize()
        if session and session.is_accessable and session.get_user():
            yield session
