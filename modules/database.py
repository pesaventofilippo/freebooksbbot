from pony.orm import Database, PrimaryKey, Required, Optional, Set, db_session

db = Database("sqlite", "../freebooksbbot.db", create_db=True)


class User(db.Entity):
    chatId = Required(int, unique=True)
    status = Required(str, default="normal")
    wantsNotifications = Required(bool, default=True)


class Category(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    books = Set(lambda: Book, reverse='category')


class Book(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    category = Optional(Category)


def syncFiles():
    with db_session:
        from pony.orm import select
        from os import listdir
        flist = listdir('ebooks')
        for file in flist:
            if not Book.exists(lambda b: b.name == file):
                Book(name=file)
        for dbook in select(book for book in Book)[:]:
            if dbook.name not in flist:
                dbook.delete()


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
