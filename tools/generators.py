import random
import time
from typing import List, Set


def generate_unique_number() -> str:
    time_stamp: int = round(time.time() * 100000000)
    random_num: int = random.randint(11, 99)
    return "{}{}".format(time_stamp, random_num)


def generate_ngrams(text: str, min_length: int = 2) -> List[str]:
    text = text.lower().strip()
    ngrams: Set[str] = set()

    # Add Full Text
    ngrams.add(text)

    # Add Words
    words: List[str] = text.split()
    for word in words:
        if len(word) >= min_length:
            ngrams.add(word)

    # Add Character N-Grams For Each Word
    for word in words:
        for i in range(len(word)):
            for j in range(i + min_length, len(word) + 1):
                substring: str = word[i:j]
                if len(substring) >= min_length:
                    ngrams.add(substring)

    return list(ngrams)
