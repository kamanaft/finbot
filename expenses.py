""" Working with expenses - adding, removing, statistics"""
import datetime
import re
from typing import List, NamedTuple, Optional

import pytz

import db
import exceptions
from categories import Categories


class Message(NamedTuple):
    """Structure of the parsed message about the new expense"""
    amount: int
    category_text: str


class Expense(NamedTuple):
    """Structure of the new expense added to the database"""
    id: Optional[int]
    amount: int
    category_name: str


def add_expense(raw_message: str) -> Expense:
    """Adds a new expense.
    Takes as input the text of the message that came to the bot."""
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(
        parsed_message.category_text)
    inserted_row_id = db.insert("expense", {
        "amount": parsed_message.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message
    })
    return Expense(id=None,
                   amount=parsed_message.amount,
                   category_name=category.name)


def get_today_statistics() -> str:
    """Returns today's expense statistics as a string"""
    cursor = db.get_cursor()
    cursor.execute("select sum(amount)"
                   "from expense where date(created)=date('now', 'localtime')")
    result = cursor.fetchone()
    if not result[0]:
        return "Dnes zatím žádné výdaje"
    all_today_expenses = result[0]
    cursor.execute("select sum(amount) "
                   "from expense where date(created)=date('now', 'localtime') "
                   "and category_codename in (select codename "
                   "from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Dnešní výdaje:\n"
            f"Celkem — {all_today_expenses} Kč\n"
            f"Základní — {base_today_expenses} Kč z {_get_budget_limit()} Kč\n\n"
            f"Aktuální měsíc: /month")


def get_month_statistics() -> str:
    """Returns the current month's expense statistics as a string"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}'")
    result = cursor.fetchone()
    if not result[0]:
        return "Tento měsíc zatím žádné výdaje"
    all_today_expenses = result[0]
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Výdaje v aktuálním měsíci:\n"
            f"Celkem — {all_today_expenses} Kč.\n"
            f"Základní — {base_today_expenses} Kč z "
            f"{now.day * _get_budget_limit()} Kč")


def last() -> List[Expense]:
    """Returns the last few expenses"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], category_name=row[2]) for row in rows]
    return last_expenses


def delete_expense(row_id: int) -> None:
    """Deletes a message by its identifier"""
    db.delete("expense", row_id)


def _parse_message(raw_message: str) -> Message:
    """Parses the text of the message about the new expense."""
    regexp_result = re.match(r"([\d ]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Nerozumím tomu sdělení. Napište zprávu ve formátu, "
            "třeba:\n500 taxi")

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    return Message(amount=amount, category_text=category_text)


def _get_now_formatted() -> str:
    """Returns today's date as a string"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Returns today's datetime, taking into account the Prague time zone."""
    tz = pytz.timezone("Europe/Prague")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit() -> int:
    """Returns the daily spending limit for basic base spending"""
    return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]
