from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from pony.orm import db_session, select
from modules.database import Book, Category


@db_session
def category(book_id, msg_id):
    keyboard = []
    line = []
    linecount = 0
    for cat in select(c for c in Category if c.name != "General")[:]:
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
def movebook(msg_id, show_all=False):
    keyboard = []
    for book in select(b for b in Book)[:]:
        if show_all or (book.category.name == "General"):
            keyboard.append([InlineKeyboardButton(text=book.name, callback_data="mvbook_{}#{}".format(book.id, msg_id))])
    if not show_all:
        keyboard.append([InlineKeyboardButton(text="📚 Show All Books", callback_data="moveall#{}".format(msg_id))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def delbook(msg_id, show_all=False):
    keyboard = []
    for book in select(b for b in Book)[:]:
        if show_all or (book.category.name == "General"):
            keyboard.append([InlineKeyboardButton(text=book.name, callback_data="delbook_{}#{}".format(book.id, msg_id))])
    if not show_all:
        keyboard.append([InlineKeyboardButton(text="📚 Show All Books", callback_data="delall#{}".format(msg_id))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@db_session
def search_cat(msg_id):
    keyboard = []
    line = []
    linecount = 0
    for cat in select(c for c in Category if c.books)[:]:
        linecount += 1
        if linecount > 2:
            linecount = 1
            keyboard.append(line)
            line = []
        line.append(InlineKeyboardButton(text=cat.name, callback_data="searchcat_{}#{}".format(cat.id, msg_id)))
    if line:
        keyboard.append(line)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_search(msg_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="backsearch#{}".format(msg_id))]
    ])
