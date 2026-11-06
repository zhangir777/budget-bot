"""Text reports and Excel export."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font


def money(x: float, cur: str = "₸") -> str:
    s = f"{x:,.2f}".rstrip("0").rstrip(".").replace(",", " ")
    return f"{s} {cur}"


def summary_text(title: str, s: dict, limit: float | None, cur: str = "₸") -> str:
    lines = [
        f"📊 {title}",
        f"Income: {money(s['income'], cur)}",
        f"Spent: {money(s['expense'], cur)}",
        f"Balance: {money(s['income'] - s['expense'], cur)}",
    ]
    if s["by_category"]:
        lines.append("")
        lines += [f"• {c}: {money(v, cur)}" for c, v in s["by_category"].items()]
    if limit:
        pct = s["expense"] / limit * 100
        lines.append(f"\nLimit: {money(limit, cur)} ({pct:.0f}% used)")
        if pct >= 100:
            lines.append("⚠️ The monthly limit is exceeded.")
        elif pct >= 80:
            lines.append("⚠️ You have used more than 80% of the limit.")
    return "\n".join(lines)


def export_xlsx(rows: list[tuple], path: Path) -> Path:
    """rows: (date, is_income, category, amount, note). Opens in Excel and Google Sheets."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Entries"
    ws.append(["Date", "Type", "Category", "Amount", "Note"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for date, is_income, cat, amount, note in rows:
        kind = "Income" if is_income else "Expense"
        ws.append([date.replace("T", " "), kind, cat, amount, note])
    for col, w in zip("ABCDE", (20, 10, 14, 12, 30), strict=True):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    wb.save(path)
    return path
