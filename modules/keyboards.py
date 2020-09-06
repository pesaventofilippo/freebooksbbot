from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from pony.orm import db_session, select
from modules.database import Book, Category


@db_session
def manageBooks(actionStr, msg_id, show_all=False):
    keyboard = []
    books = select(b for b in Book)[:]
    for book in sorted(books, key=lambda x: x.name):
        if show_all or (book.category.name == "General"):
            keyboard.append([InlineKeyboardButton(text=book.name, callback_data=f"{actionStr}book_{book.id}#{msg_id}")])
    if not show_all:
        keyboard.append([InlineKeyboardButton(text="📚 Show All Books", callback_data=f"{actionStr}all#{msg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def category(book_id, msg_id):
    keyboard = []
    line = []
    linecount = 0
    categories = select(c for c in Category if c.name != "General")[:]
    for cat in sorted(categories, key=lambda x: x.name):
        linecount += 1
        if linecount > 2:
            linecount = 1
            keyboard.append(line)
            line = []
        line.append(InlineKeyboardButton(text=cat.name, callback_data=f"selcat_{cat.id}_{book_id}#{msg_id}"))
    if line:
        keyboard.append(line)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def search_cat(msg_id):
    keyboard = []
    line = []
    linecount = 0
    categories = select(c for c in Category if c.books)[:]
    for cat in sorted(categories, key=lambda x: x.name):
        linecount += 1
        if linecount > 2:
            linecount = 1
            keyboard.append(line)
            line = []
        line.append(InlineKeyboardButton(text=cat.name, callback_data=f"searchcat_{cat.id}#{msg_id}"))
    if line:
        keyboard.append(line)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_search(msg_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data=f"backsearch#{msg_id}")]
    ])
