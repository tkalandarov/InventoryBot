import asyncio
import sys
from contextlib import suppress
from aiogram import types, Router, F
from app.loader import dp, bot
from app.keyboards.reply import *
from app.keyboards.inline import *
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from app.filters.role_filter import RoleCheck
from app.states.worker_states import *
from app.db.operations import *
from app.middlewares.articles import *
from app.middlewares.misc import *
from app.utils.callback_factories import RedactStoredItem
from aiogram.exceptions import TelegramBadRequest

router = Router()

"""
Create new stored item
"""


@router.message(F.text.lower() == "новый товар", RoleCheck("worker"))
async def new_stored_item_setup(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите номер артикула:",
        reply_markup=reply_row_menu(['Отмена'])
    )
    await state.set_state(NewStoredItem.article)


@router.message(F.text, RoleCheck("worker"), NewStoredItem.article)
async def new_stored_item_article_process(message: types.Message, state: FSMContext):
    article = message.text
    if not (await article_guard(article)):
        # If article doesn't exist
        buttons = [types.InlineKeyboardButton(text="Создать новую запись", callback_data=f"create.{article}")]
        await message.answer(
            f"Товар с артикулом: {article} не найден.",
            reply_markup=inline_row_menu(buttons),
        )
    else:
        await message.answer(
            "Товар с таким артикулом уже существует.", reply_markup=get_menu()
        )
    await state.clear()


@router.callback_query(F.data.startswith('create'), RoleCheck("worker"))
async def create_item_callback(callback: types.CallbackQuery, state: FSMContext):
    articleNumber = callback.data.split(".")[1]
    await state.update_data(articleNumber=articleNumber)
    await state.set_state(NewStoredItem.category)
    await callback.message.answer(
        "Укажите категорию товара:", reply_markup=reply_row_menu(["Отмена"])
    )
    await callback.answer()


@router.message(NewStoredItem.category, RoleCheck("worker"), F.text)
async def create_item_category_callback(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(NewStoredItem.subcategory)

    await message.answer(
        "Укажите подкатегорию товара:", reply_markup=reply_row_menu(["Отмена"])
    )


@router.message(NewStoredItem.subcategory, RoleCheck("worker"), F.text)
async def create_item_subcategory_callback(message: types.Message, state: FSMContext):
    await state.update_data(subcategory=message.text)
    await state.set_state(NewStoredItem.name)

    await message.answer(
        "Укажите наименование товара:", reply_markup=reply_row_menu(["Отмена"])
    )


@router.message(NewStoredItem.name, RoleCheck("worker"), F.text)
async def create_item_name_callback(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(NewStoredItem.quantity)

    await message.answer(
        "Укажите количество товара (шт.):", reply_markup=reply_row_menu(["Отмена"])
    )


@router.message(NewStoredItem.quantity, RoleCheck("worker"), F.text)
async def create_item_quantity_callback(message: types.Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await state.set_state(NewStoredItem.photo)

    await message.answer(
        "Прикрепите фотографию товара. Если таковой нет, отправьте любое текстовое сообщение:",
        reply_markup=reply_row_menu(["Отмена"]),
    )


@router.message(NewStoredItem.photo, RoleCheck("worker"))
async def create_item_photo_callback(message: types.Message, state: FSMContext):
    try:
        await state.update_data(photo=message.photo[-1].file_id)
    except Exception as e:
        print(
            "Exception at uploading photo for a new item. Using blank instead.",
            file=sys.stderr,
        )
        await state.update_data(photo='-')
    await state.set_state(NewStoredItem.confirmation)
    data = await state.get_data()
    answer_text = "Вы собираетесь добавить новую запись:\n"

    answer_text += f"\nАртикул: {data['articleNumber']}"
    answer_text += f"\nКатегория: {data['category']}"
    answer_text += f"\nПодкатегория: {data['subcategory']}"
    answer_text += f"\nНазвание: {data['name']}"
    answer_text += f"\nКоличество (шт.): {data['quantity']}"

    answer_text += (
        f"\n\nОтправьте 'Да' (в любом регистре) для подтверждения своих действий."
    )
    await message.answer(answer_text, reply_markup=reply_row_menu(["Отмена"]))


@router.message(NewStoredItem.confirmation, RoleCheck("worker"), F.text.lower() == "да")
async def create_item_confirmation_callback(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sql = f"""INSERT INTO storeditems(articleNumber, 
    category, subcategory, 
    name, quantity, photo)
    VALUES ($1, $2, $3, $4, $5, $6)"""  # that's a mess, ngl, but you should deal with it

    try:
        await custom_sql(
            sql,
            data["articleNumber"],
            data["category"],
            data["subcategory"],
            data["name"],
            int(data["quantity"]),
            data["photo"],
            execute=True,
        )
        answer_text = "Запись внесена."
    except Exception as e:
        answer_text = f"Возникла ошибка при создании записи: {e}"
    await message.answer(answer_text, reply_markup=get_menu())
    await state.clear()


"""
Items Manipulation
"""


@router.callback_query(RedactStoredItem.filter(F.action.startswith("change_")), RoleCheck("worker"))
async def edit_item_callback(callback: types.CallbackQuery, state: FSMContext, callback_data: RedactStoredItem):
    await state.set_state(RedactStoredItemState.change)
    action = callback_data.action.split('_')[-1]

    answers = {
        "articlenumber": "Введите новый артикул товара:",
        "category": "Введите новую категорию товара:",
        "subcategory": "Введите новую подкатегорию товара:",
        "name": "Введите новое название товара:",
        "quantity": "Введите количество товара:",
        "photo": "Отправьте фотографию товара:",
        "transactions": "Выберите действие:",
    }
    try:
        if action == "transactions":
            await state.update_data(articleNumber=callback_data.articleNumber)
            await callback.message.answer(
                answers[action],
                reply_markup=reply_row_menu(["История транзакций", "Новая транзакция", "Отмена"]),
            )
        else:
            await callback.message.answer(answers[action], reply_markup=reply_row_menu(["Отмена"]))
        await state.update_data(articleNumber=callback_data.articleNumber, action=action)
    except Exception as e:
        await callback.message.answer(
            "Возникла непредвиденная ошибка. Обратитесь к администратору.",
            reply_markup=reply_row_menu(["Главное меню"])
        )
    await callback.answer()


@router.message(RedactStoredItemState.change, RoleCheck("worker"))
async def change_item_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']
    articleNumber = data['articleNumber']

    is_correct = True  # incorrect info will be flagged as false
    sql = None

    if action == 'photo':
        photo_id = message.photo[-1].file_id if message.photo is not None else '-'
        sql = f"UPDATE storeditems SET photo = $1 WHERE articleNumber = $2"
        await custom_sql(sql, photo_id, data["articleNumber"], execute=True)
    elif action == 'transactions':
        await state.update_data(articleNumber=articleNumber)
        if message.text.lower() == "история транзакций":
            await view_transaction_history(message, state)
        elif message.text.lower() == "новая транзакция":
            await start_new_transaction(message, state)
        else:
            await message.answer("Действие отменено.", reply_markup=get_menu())
        is_correct = False # skip clearing state and confirmation
    elif message.text is not None:
        sql = f"UPDATE storeditems SET {action} = $1 WHERE articleNumber = $2"
        if action in ["quantity"]:
            await custom_sql(
                sql, int(message.text), data["articleNumber"], execute=True
            )
        else:
            await custom_sql(sql, message.text, data['articleNumber'], execute=True)
    else:
        await message.answer(
            "Ошибка: некорректная информация.",
            reply_markup=reply_row_menu(['Главное меню'])
        )
        is_correct = False

    if is_correct:
        await state.clear()
        await message.answer("Изменения внесены.", reply_markup=get_menu())


@router.callback_query(RedactStoredItem.filter(F.action.startswith("delete")), RoleCheck("worker"))
async def delete_item_process(callback: types.CallbackQuery, callback_data=RedactStoredItem):
    articleNumber = callback_data.articleNumber
    sql = f"DELETE FROM storeditems WHERE articleNumber = $1"
    await custom_sql(sql, articleNumber, execute=True)
    await callback.message.answer("Товар удален.", reply_markup=get_menu())
    await callback.answer()


"""
Create new transactions
"""


@router.message(F.text.lower() == "новая транзакция", RoleCheck("worker"))
async def start_new_transaction(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите тип транзакции:", reply_markup=get_transaction_type_menu()
    )
    await state.set_state(NewTransaction.transaction_type)

@router.message(NewTransaction.transaction_type, RoleCheck("worker"))
async def process_transaction_type(message: types.Message, state: FSMContext):
    transaction_type = message.text.lower()
    if transaction_type not in ["приход", "продажа"]:
        await message.answer(
            "Некорректный тип транзакции. Пожалуйста, выберите 'Приход' или 'Продажа'.",
            reply_markup=get_transaction_type_menu(),
        )
        return
    await state.update_data(transaction_type="add" if transaction_type == "приход" else "sell")
    await state.set_state(NewTransaction.quantity)
    await message.answer("Введите количество:")


@router.message(NewTransaction.quantity, RoleCheck("worker"))
async def process_quantity(message: types.Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await state.set_state(NewTransaction.confirmation)
    data = await state.get_data()
    transaction_display = "приход" if data["transaction_type"] == "add" else "продажа"
    await message.answer(
        f"Подтвердите транзакцию:\n"
        f"Артикул товара: {data['articleNumber']}\n"
        f"Тип транзакции: {transaction_display}\n"
        f"Количество: {data['quantity']}\n"
        f"Введите 'да' для подтверждения или 'нет' для отмены."
    )


@router.message(NewTransaction.confirmation, RoleCheck("worker"))
async def confirm_transaction(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        data = await state.get_data()
        # Retrieve item_id using articleNumber
        sql_get_item_id = "SELECT id FROM storeditems WHERE articleNumber = $1"
        item_id_result = await custom_sql(sql_get_item_id, data["articleNumber"], fetch=True)

        if not item_id_result:
            await message.answer("Ошибка: товар с указанным артикулом не найден.", reply_markup=get_menu())
            await state.clear()
            return

        item_id = item_id_result[0]["id"]

        # Insert new transaction
        sql_insert_transaction = """
                INSERT INTO transactions (item_id, transaction_type, quantity, userid)
                VALUES ($1, $2, $3, $4)
                """
        await custom_sql(
            sql_insert_transaction,
            item_id,
            data["transaction_type"],
            int(data["quantity"]),
            message.from_user.id,
            execute=True,
        )

        # Update storeditems quantity
        update_quantity_sql = """
            UPDATE storeditems
            SET quantity = quantity + $1
            WHERE id = $2
        """
        quantity_change = int(data["quantity"]) if data["transaction_type"] == "add" else -int(data["quantity"])
        await custom_sql(update_quantity_sql, quantity_change, item_id, execute=True)
        await message.answer("Транзакция успешно добавлена.", reply_markup=get_menu())
    else:
        await message.answer("Транзакция отменена.", reply_markup=get_menu())
    await state.clear()


"""
Transactions manipulation
"""


@router.message(F.text.lower() == "история транзакций", RoleCheck("worker"))
async def view_transaction_history(message: types.Message, state: FSMContext):
    data = await state.get_data()
    articleNumber = data["articleNumber"]
    sql = """
    SELECT t.id, t.transaction_type, t.quantity, t.transaction_date, t.userid
    FROM transactions t
    JOIN storeditems s ON t.item_id = s.id
    WHERE s.articleNumber = $1
    ORDER BY t.transaction_date DESC
    """
    transactions = await custom_sql(sql, articleNumber, fetch=True)
    if transactions:
        history = "\n".join(
            [
                f"ID: {t['id']}, Тип: {'Приход' if t['transaction_type'] == 'add' else 'Продажа'}, Количество: {t['quantity']}, Дата: {t['transaction_date'].strftime('%d.%m.%Y %H:%M')}, Пользователь: {t['userid']}"
                for t in transactions
            ]
        )

        await message.answer(
            f"История транзакций для артикула {articleNumber}:\n{history}",
            reply_markup=get_menu(),
        )
    else:
        await message.answer(
            f"История транзакций для артикула {articleNumber} пуста.",
            reply_markup=get_menu(),
        )
    await state.clear()


@router.message(F.text.lower() == "удалить транзакцию", RoleCheck("worker"))
async def start_delete_transaction(message: types.Message, state: FSMContext):
    await message.answer("Введите ID транзакции для удаления:")
    await state.set_state(DeleteTransaction.transaction_id)


@router.message(DeleteTransaction.transaction_id, RoleCheck("worker"))
async def process_delete_transaction_id(message: types.Message, state: FSMContext):
    transaction_id = message.text
    sql = "DELETE FROM transactions WHERE transaction_id = $1"
    await custom_sql(sql, transaction_id, execute=True)
    await message.answer("Транзакция успешно удалена.", reply_markup=get_menu())
    await state.clear()
