"""Budget bot: send '250 coffee' to add an expense, '+50000 salary' to add income.

Run: python -m bot.main   (needs BOT_TOKEN in .env)
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import FSInputFile, Message
from dotenv import load_dotenv

from bot.db import Store
from bot.parser import parse_entry
from bot.report import export_xlsx, money, summary_text

router = Router()
CUR = "₸"

HELP = (
    "Hi! I track your money.\n\n"
    "Send one line:\n"
    "250 coffee  or  taxi 1500  is an expense\n"
    "+50000 salary  is income\n\n"
    "/today - today's totals\n"
    "/month - this month by category\n"
    "/last - last 10 entries\n"
    "/undo - delete the last entry\n"
    "/limit 200000 - monthly spending limit\n"
    "/export - Excel file (opens in Google Sheets too)"
)


def _store() -> Store:
    return router.store  # set in main()


@router.message(CommandStart())
@router.message(Command("help"))
async def start(message: Message):
    await message.answer(HELP)


@router.message(Command("today"))
async def today(message: Message):
    s = _store().summary(message.from_user.id, datetime.now().strftime("%Y-%m-%d"))
    await message.answer(summary_text("Today", s, None, CUR))


@router.message(Command("month"))
async def month(message: Message):
    uid = message.from_user.id
    s = _store().summary(uid, datetime.now().strftime("%Y-%m"))
    title = datetime.now().strftime("%B %Y")
    await message.answer(summary_text(title, s, _store().get_limit(uid), CUR))


@router.message(Command("last"))
async def last(message: Message):
    rows = _store().last(message.from_user.id)
    if not rows:
        await message.answer("No entries yet. Send for example: 250 coffee")
        return
    lines = []
    for when, amount, is_income, cat, note in rows:
        sign = "+" if is_income else "-"
        lines.append(f"{when[5:10]}  {sign}{money(amount, CUR)}  {cat}  {note}".rstrip())
    await message.answer("\n".join(lines))


@router.message(Command("undo"))
async def undo(message: Message):
    row = _store().undo(message.from_user.id)
    if not row:
        await message.answer("Nothing to undo.")
        return
    amount, is_income, cat, note = row
    sign = "+" if is_income else "-"
    await message.answer(f"Deleted: {sign}{money(amount, CUR)} {cat} {note}".rstrip())


@router.message(Command("limit"))
async def limit(message: Message, command: CommandObject):
    entry = parse_entry(command.args or "")
    if not entry:
        await message.answer("Usage: /limit 200000")
        return
    _store().set_limit(message.from_user.id, entry.amount)
    await message.answer(f"Monthly limit set: {money(entry.amount, CUR)}")


@router.message(Command("export"))
async def export(message: Message):
    rows = _store().all_entries(message.from_user.id)
    if not rows:
        await message.answer("No entries to export yet.")
        return
    with tempfile.TemporaryDirectory() as tmp:
        path = export_xlsx(rows, Path(tmp) / "budget.xlsx")
        await message.answer_document(FSInputFile(path), caption=f"{len(rows)} entries")


@router.message(F.text & ~F.text.startswith("/"))
async def add_entry(message: Message):
    entry = parse_entry(message.text)
    if not entry:
        await message.answer("I did not find an amount. Example: 250 coffee  or  +50000 salary")
        return
    uid = message.from_user.id
    _store().add(uid, entry.amount, entry.is_income, entry.category, entry.note)
    sign = "+" if entry.is_income else "-"
    text = f"Saved: {sign}{money(entry.amount, CUR)} · {entry.category}"
    if entry.note:
        text += f" · {entry.note}"
    limit_value = _store().get_limit(uid)
    if limit_value and not entry.is_income:
        spent = _store().summary(uid, datetime.now().strftime("%Y-%m"))["expense"]
        if spent >= limit_value:
            text += f"\n⚠️ Monthly limit exceeded: {money(spent, CUR)} of {money(limit_value, CUR)}"
        elif spent >= 0.8 * limit_value:
            text += f"\n⚠️ {spent / limit_value:.0%} of the monthly limit is used"
    await message.answer(text)


async def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    db_path = os.environ.get("DB_PATH", "data/budget.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    router.store = Store(db_path)
    bot = Bot(os.environ["BOT_TOKEN"])
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
