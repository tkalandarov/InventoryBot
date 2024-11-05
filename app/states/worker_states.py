from aiogram.fsm.state import State, StatesGroup

class NewStoredItem(StatesGroup):
    article = State()
    category = State()
    subcategory = State()
    name = State()
    quantity = State()
    photo = State()
    confirmation = State()

class RedactStoredItemState(StatesGroup):
    change = State()

class NewTransaction(StatesGroup):
    transaction_type = State()
    quantity = State()
    confirmation = State()

class DeleteTransaction(StatesGroup):
    transaction_id = State()