from datetime import date
from typing import Union

from django.core.validators import *
from django.core.validators import ValidationError
from emoji_regex import emoji_regex

__all__ = [
    "OrValidator",
    "RegexValidator",
    "URLValidator",
    "EmailValidator",
    "GmailValidtor",
    "MobileValidtor",
    "MinValueValidator",
    "MaxValueValidator",
    "MinLengthValidator",
    "MaxLengthValidator",
    "PersianLetterValidator",
    "FullPersianLetterValidator",
    "EmojiValidtor",
    "NotInPastValidtor",
    "NotInFutureValidtor",
    "NationalCodeValidator",
]

from tools.datetimes import dt


class BaseValidator:
    def __eq__(self, other):
        # Check Equality For Serialization
        return isinstance(other, FullPersianLetterValidator)

    def deconstruct(self):
        # Return Tuple For Serialization: (Path, Args, Kwargs)
        path: str = "{}.{}".format(self.__class__.__module__, self.__class__.__qualname__)
        return path, [], {}


class OrValidator(BaseValidator):
    def __init__(self, validators):
        self.validators = validators

    def __call__(self, value):
        errors = []
        for validator in self.validators:
            try:
                validator(value)
                return
            except ValidationError as e:
                errors.append(e.error_list)
        raise ValidationError(errors)


class PersianLetterValidator(BaseValidator):
    def __call__(self, value):
        if not re.match(
            r"^[آ-ی ۰-۹ \u200C\u060C\u061F\u061B\u00AB\u00BB؟،.!؟«»]+$", value
        ):
            raise ValidationError("Must be all Persian letters.")


class FullPersianLetterValidator(BaseValidator):
    def __call__(self, value):
        if not re.match(r"^[آ-ی \u200C]+$", value):
            raise ValidationError(
                "Must be all Persian letters. It must not contain any numbers or symbols."
            )


class MobileValidtor(BaseValidator):
    def __call__(self, value):
        if not re.match(r"^09\d{9}$", value):
            raise ValidationError("Must be a standard mobile like 0910*******.")


class GmailValidtor(BaseValidator):
    def __call__(self, value):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", value):
            raise ValidationError("Must be a gmail.")


class MinimumAgeValidator(BaseValidator):
    def __init__(self, min_years):
        self.min_years = min_years

    def __call__(self, value):
        # Calculate The Minimum Acceptable Date
        today = date.today()
        min_date = date(today.year - self.min_years, today.month, today.day)

        if value > min_date:
            raise ValidationError(
                "The date must be at least {} years ago.".format(self.min_years)
            )


class EmojiValidtor(BaseValidator):
    def __call__(self, value):
        if not re.match(emoji_regex, value):
            raise ValidationError("Must be an Emoji.")


class NationalCodeValidator(BaseValidator):

    @staticmethod
    def is_valid(ncode: str) -> bool:
        if len(ncode) != 10:
            return False
        if ncode in [10 * str(i) for i in range(10)]:
            return False

        total: int = 0

        for i, l in enumerate(ncode[:-1]):
            total += (10 - i) * int(l)

        if ((total % 11 < 2) and (int(ncode[-1]) == (total % 11))) or (
            (total % 11 >= 2) and (int(ncode[-1]) == (11 - (total % 11)))
        ):
            return True
        return False

    def __call__(self, value):
        if not self.is_valid(value):
            raise ValidationError("NCode is Invalid.")


class NotInFutureValidtor(BaseValidator):
    def __call__(self, value: Union[dt.date, dt.datetime]):
        now = dt.datetime.now()
        if (isinstance(value, dt.date) and now.date() < value) or (
            isinstance(value, dt.datetime) and now < value
        ):
            raise ValidationError("Must be in past")


class NotInPastValidtor(BaseValidator):
    def __call__(self, value: Union[dt.date, dt.datetime]):
        now = dt.datetime.now()
        if (isinstance(value, dt.date) and now.date() > value) or (
            isinstance(value, dt.datetime) and now > value
        ):
            raise ValidationError("Must be in future")
