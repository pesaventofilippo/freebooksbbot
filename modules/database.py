from pony.orm import Database, Required, Optional, Set

db = Database("sqlite", "../freebooksbbot.db", create_db=True)


class User(db.Entity):
    chatId = Required(int, unique=True)
    status = Required(str, default="normal")
    wantsNotifications = Required(bool, default=True)


class Category(db.Entity):
    name = Required(str, unique=True)
    books = Set(lambda: Book, reverse='category')


class Book(db.Entity):
    name = Required(str, unique=True)
    telegramFileId = Required(str, unique=True)
    category = Optional(Category)


db.generate_mapping(create_tables=True)
