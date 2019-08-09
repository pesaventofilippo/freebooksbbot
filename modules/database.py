from pony.orm import Database, Required, Optional, Set, db_session, commit
from modules.helpers import supportedOsFile

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
    category = Optional(Category)


@db_session
def syncFiles():
    from pony.orm import select
    from os import listdir
    if not Category.exists(lambda c: c.name == "General"):
        Category(name="General")
        commit()
    flist = listdir('ebooks')
    for dbook in select(book for book in Book)[:]:
        if dbook.name not in flist:
            dbook.delete()
    blist = [book.name for book in select(b for b in Book)[:]]
    for fbook in flist:
        if fbook not in blist and supportedOsFile(fbook):
            Book(name=fbook, category=Category.get(name="General"))


if __name__ == "__main__":
    from sys import argv
    if "--reset-books" in argv:
        db.drop_table('Book', if_exists=True, with_all_data=True)
        print("Book Table successfully deleted!")
    if "--reset-categories" in argv:
        db.drop_table('Category', if_exists=True, with_all_data=True)
        print("Category Table successfully deleted!")
    if "--sync-files" in argv:
        db.generate_mapping(create_tables=True)
        syncFiles()
        print("File list successfully synced!")
else:
    db.generate_mapping(create_tables=True)
    syncFiles()
