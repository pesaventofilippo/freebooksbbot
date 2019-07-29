from pony.orm import Database, Required

db = Database("sqlite", "../freebooksbbot.db", create_db=True)


class User(db.Entity):
    chatId = Required(int, unique=True)
    status = Required(str, default="normal")
    wantsNotifications = Required(bool, default=True)


db.generate_mapping(create_tables=True)
