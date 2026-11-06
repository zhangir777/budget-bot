from datetime import datetime

from bot.db import Store
from bot.report import export_xlsx, money, summary_text


def make(tmp_path):
    return Store(str(tmp_path / "t.db"))


def test_summary_and_undo(tmp_path):
    s = make(tmp_path)
    now = datetime(2026, 11, 6, 12, 0)
    s.add(1, 250, False, "Food", "coffee", now)
    s.add(1, 1500, False, "Transport", "taxi", now)
    s.add(1, 50000, True, "Income", "salary", now)
    s.add(2, 999, False, "Food", "other user", now)
    r = s.summary(1, "2026-11")
    assert r["income"] == 50000 and r["expense"] == 1750
    assert list(r["by_category"]) == ["Transport", "Food"]
    assert s.summary(1, "2026-10")["expense"] == 0
    assert s.undo(1)[:2] == (50000, 1)
    assert s.summary(1, "2026-11")["income"] == 0
    assert s.undo(3) is None


def test_limit(tmp_path):
    s = make(tmp_path)
    assert s.get_limit(1) is None
    s.set_limit(1, 100)
    s.set_limit(1, 200)
    assert s.get_limit(1) == 200


def test_report_and_export(tmp_path):
    s = make(tmp_path)
    s.add(1, 900, False, "Food", "pizza", datetime(2026, 11, 6))
    text = summary_text("November", s.summary(1, "2026-11"), 1000, "₸")
    assert "Food: 900 ₸" in text and "90% used" in text and "80%" in text
    assert money(1234567.5) == "1 234 567.5 ₸"
    path = export_xlsx(s.all_entries(1), tmp_path / "x.xlsx")
    assert path.exists() and path.stat().st_size > 0
