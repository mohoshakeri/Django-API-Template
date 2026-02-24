from typing import Dict, Optional

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from tools.datetimes import dt


def create_token(key: str, data: Dict, expire_minutes: int) -> str:
    payload: Dict = {
        **data,
        "exp": dt.datetime.now() + dt.timedelta(minutes=expire_minutes),
    }
    token: str = jwt.encode(payload, key, algorithm="HS256")
    return token


def decode_token(key: str, token: str) -> Optional[Dict]:
    try:
        decoded: Dict = jwt.decode(token, key, algorithms=["HS256"])
        return decoded
    except (ExpiredSignatureError, InvalidTokenError):
        return None
