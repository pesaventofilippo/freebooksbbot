from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from pony.orm import db_session


@db_session
def category(book_id, msg_id):
    from pony.orm import select
    from modules.database import Category
    keyboard = []
    line = []
    linecount = 0
    for cat in select(c for c in Category)[:]:
        linecount += 1
        if linecount > 2:
            linecount = 1
            keyboard.append(line)
            line = []
        line.append(InlineKeyboardButton(text=cat.name, callback_data="selcat_{}_{}#{}".format(cat.id, book_id, msg_id)))
    if line:
        keyboard.append(line)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def movebook(msg_id):
    from pony.orm import select
    from modules.database import Book
    keyboard = []
    for book in select(b for b in Book if b.category.name == "General")[:]:
        keyboard.append([InlineKeyboardButton(text=book.name, callback_data="mvbook_{}#{}".format(book.id, msg_id))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def search_cat(msg_id):
    from pony.orm import select
    from modules.database import Category
    keyboard = []
    line = []
    linecount = 0
    for cat in select(c for c in Category)[:]:
        linecount += 1
        if linecount > 2:
            linecount = 1
            keyboard.append(line)
            line = []
        line.append(InlineKeyboardButton(text=cat.name, callback_data="searchcat_{}#{}".format(cat.id, msg_id)))
    if line:
        keyboard.append(line)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def search_book(cat_id, msg_id):
    from pony.orm import select
    from modules.database import Book
    keyboard = []
    for book in select(b for b in Book if b.category.id == cat_id)[:]:
        keyboard.append([InlineKeyboardButton(text=book.name, callback_data="getbook_{}#{}".format(book.id, msg_id))])
    keyboard.append([InlineKeyboardButton(text="◀️ Back", callback_data="backsearch#{}".format(msg_id))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
