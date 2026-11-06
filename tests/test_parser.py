import pytest

from bot.parser import parse_entry


@pytest.mark.parametrize(
    ("text", "amount", "income", "cat", "note"),
    [
        ("250 coffee", 250, False, "Food", "coffee"),
        ("taxi 1500", 1500, False, "Transport", "taxi"),
        ("1 500 такси домой", 1500, False, "Transport", "такси домой"),
        ("+50000 salary", 50000, True, "Income", "salary"),
        ("12,5 lunch", 12.5, False, "Food", "lunch"),
        ("300", 300, False, "Other", ""),
        ("-99 something odd", 99, False, "Other", "something odd"),
    ],
)
def test_parse(text, amount, income, cat, note):
    e = parse_entry(text)
    assert (e.amount, e.is_income, e.category, e.note) == (amount, income, cat, note)


@pytest.mark.parametrize("text", ["", "hello", "0 coffee", "coffee", None])
def test_no_amount(text):
    assert parse_entry(text) is None
