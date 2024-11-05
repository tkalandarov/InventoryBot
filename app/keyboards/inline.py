from aiogram import types
import sys
from app.utils.callback_factories import *
from aiogram.utils.keyboard import InlineKeyboardBuilder

def delete_log_keyboard(path: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    
    buttons = [
        {'text': 'Удалить все логи', 'action': 'delete_all_logs', 'path': None},
        {'text': 'Удалить текущий лог', 'action': 'delete_current_log', 'path': path}
    ]

    for button in buttons:
        builder.button(
            text = button['text'], callback_data=LogsInfo(action=button['action'], path=button['path']).pack()
        )
    builder.adjust(len(buttons), 0)

    return builder.as_markup()

def get_dashboard_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    buttons = [
        types.InlineKeyboardButton(text="Изменить greet_user", callback_data="changegreet_user"),
        types.InlineKeyboardButton(text="Изменить greet_stranger", callback_data="changegreet_stranger"),
        types.InlineKeyboardButton(text="Сделать бэкап", callback_data="backup_download"),
        types.InlineKeyboardButton(text="Загрузить бэкап", callback_data="backup_upload"), #todo
        types.InlineKeyboardButton(text="Просмотреть логи", callback_data="logs"),
        types.InlineKeyboardButton(text="Перезагрузка", callback_data="reboot")
    ]
    
    for i in range(0, len(buttons)-1, 2):
        builder.row(buttons[i], buttons[i+1])

    if len(buttons)%2==1:
        builder.row(buttons[-1])

    return builder.as_markup()

def inline_column_menu(buttons) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    
    for i in range(0, len(buttons)-1, 2):
        builder.row(buttons[i], buttons[i+1])

    if len(buttons)%2==1:
        builder.row(buttons[-1])

    return builder.as_markup()

def inline_row_menu(buttons) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    
    for button in buttons:
        builder.row(button)
    builder.adjust(len(buttons), 0)
    return builder.as_markup()

def get_redact_menu(articleNumber: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    buttons = [
        {'text': 'Артикул', 'action': 'change_articlenumber', 'articleNumber': articleNumber},
        {'text': 'Категория', 'action': 'change_category', 'articleNumber': articleNumber},
        {'text': 'Подкатегория', 'action': 'change_subcategory', 'articleNumber': articleNumber},
        {'text': 'Наименование', 'action': 'change_name', 'articleNumber': articleNumber},
        #{'text': 'Количество', 'action': 'change_quantity', 'articleNumber': articleNumber},
        {'text': 'Фотография', 'action': 'change_photo', 'articleNumber': articleNumber},
        {'text': 'Транзакции', 'action': 'change_transactions', 'articleNumber': articleNumber},
        {'text': 'Удалить товар', 'action': 'delete', 'articleNumber': articleNumber},
    ]
    for button in buttons:
        builder.button(
            text = button['text'], callback_data=RedactStoredItem(action=button['action'], articleNumber=button['articleNumber']).pack()
        )
    builder.adjust(2)
    
    return builder.as_markup()