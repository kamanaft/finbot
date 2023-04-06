"""Server Telegram bota spuštěný přímo."""
import logging
import os
from dotenv import load_dotenv, find_dotenv

import aiohttp
from aiogram import Bot, Dispatcher, executor, types

import exceptions
import expenses
from categories import Categories
from middlewares import AccessMiddleware

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
ACCESS_ID = os.getenv("TELEGRAM_ACCESS_ID")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(AccessMiddleware(ACCESS_ID))


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Sends a welcome message and bot help"""
    await message.answer(
        "Finanční účetní bot\n\n"
        "Přidat výdaje: 250 taxík\n"
        "Dnešní statistiky: /today\n"
        "Pro aktuální měsíc: /month\n"
        "Nedávno vzniklé výdaje: /expenses\n"
        "Kategorie výdajů: /categories")


@dp.message_handler(lambda message: message.text.startswith('/del'))
async def del_expense(message: types.Message):
    """Deletes one flow record by its identifier"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = "Smazáno"
    await message.answer(answer_message)


@dp.message_handler(commands=['categories'])
async def categories_list(message: types.Message):
    """Sends the list of expense categories"""
    categories = Categories().get_all_categories()
    answer_message = "Kategorie výdajů:\n\n* " +\
            ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in categories]))
    await message.answer(answer_message)


@dp.message_handler(commands=['today'])
async def today_statistics(message: types.Message):
    """Sends today's spending statistics"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['month'])
async def month_statistics(message: types.Message):
    """Sends current month's spending statistics"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['expenses'])
async def list_expenses(message: types.Message):
    """Sends the last few expense records"""
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer("Výdaje ještě nebyly zadány")
        return

    last_expenses_rows = [
        f"{expense.amount} Kč na {expense.category_name} — klikněte "
        f"/del{expense.id} pro odstranění"
        for expense in last_expenses]
    answer_message = "Nedávné uložené výdaje:\n\n* " + "\n\n* "\
            .join(last_expenses_rows)
    await message.answer(answer_message)


@dp.message_handler()
async def add_expense(message: types.Message):
    """Adds a new expence"""
    try:
        expense = expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Přidané výdaje {expense.amount} Kč na {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.reply(answer_message, reply=False)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
