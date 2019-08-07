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
            linecount = 0
            keyboard.append(line)
            line = []
        line.append(InlineKeyboardButton(text=cat.name, callback_data="selcat_{}_{}#{}".format(cat.name, book_id, msg_id)))
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
