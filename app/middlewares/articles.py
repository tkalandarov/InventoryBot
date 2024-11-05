from app.db.operations import *
from app.keyboards import get_username
import sys

async def article_guard(articleNumber):
    sql = f"SELECT EXISTS(SELECT 1 FROM storeditems WHERE articleNumber = $1)"
    result = await custom_sql(sql, articleNumber, fetchval=True)
    return result == True


async def get_item_info(articleNumber):
    sql = f"SELECT * FROM storeditems WHERE articleNumber = $1"
    result = await custom_sql(sql, articleNumber, fetchrow=True)
    print(f"resulting row at the item info is: {result}", file=sys.stderr)
    item_info = f"Информация о товаре: {articleNumber}\n"

    item_info += f"\nID товара: {result['id']}"
    item_info += f"\nАртикул: {result['articlenumber']}"
    item_info += f"\nКатегория: {result['category']}"
    item_info += f"\nПодкатегория: {result['subcategory']}"
    item_info += f"\nНазвание: {result['name']}"
    item_info += f"\nКоличество (шт.): {result['quantity']}"

    return item_info, result["photo"]


async def multiple_articles(articleNumberIncomplete):
    sql = """
    SELECT i.name, s.*
    FROM storeditems s
    JOIN storeditems i ON s.articleNumber = i.articleNumber
    WHERE s.articleNumber LIKE $1
    """
    articles = await custom_sql(sql, f"%{articleNumberIncomplete}%", fetch=True)
    if not articles:
        return False, f"Артикулов с подстрокой {articleNumberIncomplete} не найдено.", []
    else:
        articles_clear = []
        answer_text = f"Артикулы с подстрокой {articleNumberIncomplete}:\n"
        for i in range(len(articles)):
            articleNum = articles[i]["articlenumber"]
            itemName = articles[i]["name"]
            articles_clear.append(articleNum)
            answer_text += f"{i + 1}. {articleNum} - {itemName}\n"
        answer_text += f"\nВведите номер интересующего вас артикула:"
        return True, answer_text, articles_clear


async def get_transaction_history(articleNumber):
    sql = """
    SELECT t.transaction_id, t.transaction_type, t.quantity, t.transaction_date
    FROM transactions t
    JOIN storeditems i ON t.item_id = i.id
    WHERE i.articleNumber = $1
    ORDER BY t.transaction_date DESC
    """
    transactions = await custom_sql(sql, articleNumber, fetch=True)
    return transactions
