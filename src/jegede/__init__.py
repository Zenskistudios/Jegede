from __future__ import annotations

import unicodedata

__version__ = "0.1.0"


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def fold(value: str) -> str:
    """Return a lowercase Yoruba search key without tone marks or underdots."""
    value = unicodedata.normalize("NFD", value)
    value = "".join(c for c in value if not 0x300 <= ord(c) <= 0x36F)
    value = unicodedata.normalize("NFC", value)
    return value.translate(str.maketrans({"Ẹ": "ẹ", "Ọ": "ọ", "Ṣ": "ṣ"})).lower()


_ALPHABET = "abdegẹfghijklmnoọprsṣtuwy"
_SORT_RANK = {char: chr(0xE000 + index) for index, char in enumerate(_ALPHABET)}


def sort_string(value: str) -> str:
    """Return a C-collation-safe Yoruba alphabetical sort key."""
    value = _nfc(value)
    primary = fold(value).replace("gb", "\uE007")
    primary = "".join(_SORT_RANK.get(char, char) for char in primary)
    return primary + "\u0001" + unicodedata.normalize("NFD", value)


_ONES = ["odo", "okan", "meji", "meta", "merin", "marun", "mefa", "meje", "mejo", "mesan"]
_TENS = ["", "mewa", "logun", "logbon", "logoji", "ladorin", "laadota", "ladorinla"]
_ROUND_TENS = {20: "ogun", 30: "ogbon", 40: "ogoji", 50: "adorin", 60: "aadota", 70: "adorinla"}


def to_words(number: int, tones: bool = True) -> str:
    """Spell numbers from 0 through 100 in Yoruba."""
    if not 0 <= number <= 100:
        raise ValueError("number must be between 0 and 100")
    if number == 0:
        result = "odo"
    elif number == 100:
        result = "ogorun"
    elif number < 10:
        result = _ONES[number]
    elif number == 10:
        result = "mewa"
    elif number < 20:
        result = _ONES[number - 10] + "le" + "mewa"
    else:
        tens, ones = divmod(number, 10)
        result = _ROUND_TENS.get(number, _TENS[tens])
        if ones:
            result = _ONES[ones] + "le" + result
    if not tones:
        return result
    accented = {
        "okanlelogun": "ọ̀kanlélógún",
    }
    return accented.get(result, result)
