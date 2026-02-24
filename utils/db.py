import base64
import json
from hashlib import sha256
from typing import Optional, Dict, List, Any

from cryptography.fernet import Fernet
from django.db import models, transaction, IntegrityError
from django.db.models import Q, F
from project_title.settings import SECRET_KEY
from rest_framework import serializers

from CONSTANTS import (
    GET_QUERY_FILTER_SEARCH_PREFIX,
)
from tools.converters import different_persian_character_modes, md_to_html
from tools.generators import generate_ngrams

cipher_suite: Fernet = Fernet(SECRET_KEY)
db_transaction = transaction

__all__ = [
    "EncryptedField",
    "EncryptedTextField",
    "EncryptedJSONField",
    "MarkdownField",
    "EncryptedMarkdownField",
    "models",
    "db_transaction",
    "IntegrityError",
    "Q",
    "F",
]


def hash_to_db(val: str) -> str:
    val = SECRET_KEY + val
    return sha256(val.encode("utf-8")).hexdigest()


def search_by_query(search_fields: List[str], query: Optional[str] = None) -> Q:
    q_objects: Q = Q()
    if query:
        q: str = query.strip()
        q_modes: List[str] = different_persian_character_modes(q)
        q_modes_hash: List[str] = [hash_to_db(i) for i in q_modes]

        for field in search_fields:
            # Encrypted N-Grams (Partial Match)
            if field.endswith("_ngrams"):
                for q_mode_hash in q_modes_hash:
                    q_objects |= Q(**{"{}__contains".format(field): [q_mode_hash]})

            # Encrypted Hash (Exact Match)
            elif field.endswith("_hash"):
                for q_mode_hash in q_modes_hash:
                    q_objects |= Q(**{field: q_mode_hash})

            # Regular Field (Case-Insensitive Contains)
            else:
                for q_mode in q_modes:
                    q_objects |= Q(**{"{}__icontains".format(field): q_mode})

    return q_objects


class URLQueryTypeError(Exception):
    pass


def filter_objects(
    parameters: Dict[str, Any],
    filter_fields: Dict[str, Optional[List[type]]],
    convert_table: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    if convert_table:
        for exhibitive_key, original_key in convert_table.items():
            prefixed_exhibitive: str = GET_QUERY_FILTER_SEARCH_PREFIX + exhibitive_key
            if prefixed_exhibitive in parameters:
                parameters[GET_QUERY_FILTER_SEARCH_PREFIX + original_key] = parameters[
                    prefixed_exhibitive
                ]
                del parameters[prefixed_exhibitive]

    result: Dict[str, Any] = {}

    for k, v in parameters.items():
        # Skip Empty Values
        if v in [None, "", "‌", " "]:
            continue

        # Check If Parameter Is A Filter Field
        if k.startswith(GET_QUERY_FILTER_SEARCH_PREFIX):
            key_name: str = k.replace(GET_QUERY_FILTER_SEARCH_PREFIX, "")
            if key_name in filter_fields.keys():
                # Convert String Values To Appropriate Types
                if v == "none":
                    val: Any = None
                elif v == "false":
                    val: Any = False
                elif v == "true":
                    val: Any = True
                elif "," in v:
                    val: Any = v.split(",")
                else:
                    val: Any = v

                # Validate Type
                types: Optional[List[type]] = filter_fields[key_name]
                if types and not any([isinstance(val, t) for t in types]):
                    raise URLQueryTypeError(
                        "{} must be one of {}".format(key_name, types)
                    )

                result[key_name] = val

    return result


class EncryptedField(models.TextField):
    def __init__(self, *args, **kwargs) -> None:
        self.hash_field_name: Optional[str] = kwargs.pop("hash_field", None)
        self.ngram_field_name: Optional[str] = kwargs.pop("ngram_field", None)

        if self.hash_field_name is None:
            raise ValueError("Set a hash_field")
        if self.ngram_field_name is None:
            raise ValueError("Set a ngram_field")

        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        encrypted_value: bytes = cipher_suite.encrypt(value.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_value).decode("utf-8")

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[str]:
        if value is None:
            return value
        encrypted_value: bytes = base64.urlsafe_b64decode(value.encode("utf-8"))
        decrypted_value: str = cipher_suite.decrypt(encrypted_value).decode("utf-8")
        return decrypted_value

    def pre_save(self, model_instance, add):
        value: Optional[str] = getattr(model_instance, self.attname)
        if value is not None:
            # Generate Hash For Exact Matching
            hashed_value: str = hash_to_db(value)
            if self.hash_field_name:
                setattr(model_instance, self.hash_field_name, hashed_value)

            # Generate N-Grams For Partial Search
            if self.ngram_field_name:
                ngrams: List[str] = generate_ngrams(value)
                hashed_ngrams: List[str] = [hash_to_db(ngram) for ngram in ngrams]
                setattr(model_instance, self.ngram_field_name, hashed_ngrams)

        return super().pre_save(model_instance, add)

    def deconstruct(self) -> tuple:
        name, path, args, kwargs = super().deconstruct()
        kwargs["hash_field"] = self.hash_field_name
        kwargs["ngram_field"] = self.ngram_field_name
        return name, path, args, kwargs


class EncryptedJSONField(models.TextField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Optional[Any]) -> Optional[str]:
        if value is None:
            return value
        json_string: str = json.dumps(value)
        encrypted_value: bytes = cipher_suite.encrypt(json_string.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_value).decode("utf-8")

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[Any]:
        if value is None:
            return value
        encrypted_value: bytes = base64.urlsafe_b64decode(value.encode("utf-8"))
        decrypted_value: str = cipher_suite.decrypt(encrypted_value).decode("utf-8")
        return json.loads(decrypted_value)

    class Serializer(serializers.Field):
        def to_representation(self, value: Optional[Any]) -> Optional[Any]:
            if value is None:
                return None
            return value

        def to_internal_value(self, data: Optional[Any]) -> Optional[Any]:
            if data is None:
                return None
            try:
                json.dumps(data)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Invalid JSON object.")
            return data


class EncryptedTextField(models.TextField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        encrypted_value: bytes = cipher_suite.encrypt(value.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_value).decode("utf-8")

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[str]:
        if value is None:
            return value
        encrypted_value: bytes = base64.urlsafe_b64decode(value.encode("utf-8"))
        decrypted_value: str = cipher_suite.decrypt(encrypted_value).decode("utf-8")
        return decrypted_value


class MarkdownText(str):
    def as_html(self) -> str:
        return md_to_html(self)


class MarkdownField(models.TextField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if isinstance(value, MarkdownText):
            return str(value)
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return MarkdownText(value)


class EncryptedMarkdownField(models.TextField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        encrypted_value: bytes = cipher_suite.encrypt(value.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_value).decode("utf-8")

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[str]:
        if value is None:
            return value
        encrypted_value: bytes = base64.urlsafe_b64decode(value.encode("utf-8"))
        decrypted_value: str = cipher_suite.decrypt(encrypted_value).decode("utf-8")
        return MarkdownText(decrypted_value)
