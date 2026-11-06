"""Turn a chat line like '250 coffee' or '+50000 salary' into an entry."""

import re
from dataclasses import dataclass

CATEGORIES = {
    "Food": [
        "coffee",
        "lunch",
        "dinner",
        "food",
        "cafe",
        "pizza",
        "grocer",
        "market",
        "bread",
        "кофе",
        "обед",
        "ужин",
        "еда",
        "кафе",
        "пицца",
        "продукты",
        "магнит",
        "хлеб",
    ],
    "Transport": [
        "taxi",
        "bus",
        "metro",
        "fuel",
        "gas",
        "uber",
        "yandex",
        "parking",
        "такси",
        "автобус",
        "метро",
        "бензин",
        "заправка",
        "парковка",
    ],
    "Home": [
        "rent",
        "utilities",
        "internet",
        "electric",
        "water",
        "phone",
        "аренда",
        "коммуналка",
        "интернет",
        "свет",
        "вода",
        "телефон",
    ],
    "Health": [
        "pharmacy",
        "doctor",
        "dentist",
        "medicine",
        "gym",
        "аптека",
        "врач",
        "стоматолог",
        "лекарства",
        "спортзал",
    ],
    "Fun": [
        "cinema",
        "movie",
        "game",
        "bar",
        "concert",
        "netflix",
        "кино",
        "игра",
        "бар",
        "концерт",
        "подписка",
    ],
    "Shopping": ["clothes", "shoes", "shop", "gift", "одежда", "обувь", "магазин", "подарок"],
}
INCOME = "Income"
OTHER = "Other"

_AMOUNT = re.compile(r"^(?P<sign>[+-])?\s*(?P<num>\d[\d\s]*(?:[.,]\d{1,2})?)\s*(?P<rest>.*)$", re.S)
_AMOUNT_END = re.compile(r"^(?P<rest>.*?)\s+(?P<sign>[+-])?(?P<num>\d+(?:[.,]\d{1,2})?)$", re.S)


@dataclass
class Entry:
    amount: float  # always positive
    is_income: bool
    category: str
    note: str


def guess_category(note: str, is_income: bool) -> str:
    if is_income:
        return INCOME
    low = note.lower()
    for name, words in CATEGORIES.items():
        if any(w in low for w in words):
            return name
    return OTHER


def parse_entry(text: str) -> Entry | None:
    """Parse '250 coffee', 'taxi 1500', '+50000 salary', '12,5 lunch'. None if no amount."""
    text = (text or "").strip()
    sign = num = None
    rest = ""
    if m := _AMOUNT.match(text):
        sign, num, rest = m["sign"], m["num"], m["rest"]
    elif m := _AMOUNT_END.match(text):
        sign, num, rest = m["sign"], m["num"], m["rest"]
    if num is None:
        return None
    amount = float(num.replace(" ", "").replace(",", "."))
    if amount <= 0 or amount > 1e9:
        return None
    note = rest.strip()
    is_income = sign == "+"
    return Entry(amount, is_income, guess_category(note, is_income), note)
