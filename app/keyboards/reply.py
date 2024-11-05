from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def reply_row_menu(items):
    row = [types.KeyboardButton(text=item) for item in items]
    return types.ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)

def reply_column_menu(buttons):
    builder = ReplyKeyboardBuilder()
    for button in buttons:
        builder.add(types.KeyboardButton(text = button))
    builder.adjust(2)

    return builder.as_markup(resize_keyboard=True)

def get_menu():
    keyboard = reply_column_menu(["Поиск по штрих-коду", "Поиск по артикулу", "Новый товар"])

    return keyboard

def get_transaction_menu():
    keyboard = reply_column_menu(["История транзакций", "Новая транзакция", "Удалить транзакцию"])

    return keyboard

def get_transaction_type_menu():
    keyboard = reply_row_menu(["Приход", "Продажа"])

    return keyboard