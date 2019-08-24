from modules.helpers import isAdmin
from modules.database import User, Book, Category, syncFiles
from modules import keyboards
from pony.orm import select, db_session, commit
from telepot.exception import TelegramError


@db_session
def reply_text(bot, user, msg):
    name = msg['from']['first_name']
    text = msg['text']

    if user.status == "uploading_file":
        if text == "/cancel":
            user.status = "normal"
            bot.sendMessage(user.chatId, "📕 File Upload cancelled.")
        else:
            bot.sendMessage(user.chatId, "❓ Please upload an ebook file. Type /cancel to abort.")

    elif user.status.startswith("selecting_category"):
        book_id = int(user.status.split('#', 1)[1])
        book = Book.get(id=book_id)
        if text == "/cancel":
            book.category = Category.get(name="General")
            user.status = "normal"
            bot.sendMessage(user.chatId, "📗 Book moved to category <i>General</i>.", parse_mode="HTML")
            return
        categories = [cat.name.lower() for cat in select(c for c in Category)[:]]
        if text.lower() not in categories:
            cat = Category(name=text)
            commit()
            book.category = cat
            user.status = "normal"
            bot.sendMessage(user.chatId, "📗 New category <b>{}</b> successfully added!\n"
                                         "I also added the book to the new category for you.".format(text), parse_mode="HTML")
        else:
            bot.sendMessage(user.chatId, "📙 Category <b>{}</b> already exists!\n"
                                         "Try with a different name, or select one from the list above.".format(text), parse_mode="HTML")

    elif user.status == "normal":

        # Admin-only commands
        if text == "/getusers" and isAdmin(user.chatId):
            users = select(u for u in User)[:].__len__()
            bot.sendMessage(user.chatId, "👥 There currently are <b>{}</b> registered users.".format(users), parse_mode="HTML")

        elif text == "/getbooks" and isAdmin(user.chatId):
            books = [book for book in select(b for b in Book)[:]]
            res = ""
            for b in books:
                res += "\n- <b>{}</b> on <i>{}</i>".format(b.name, b.category.name)
            res = "\nBooks Database is currently empty." if not res else res
            bot.sendMessage(user.chatId, "📚 List of currently registered books:" + res, parse_mode="HTML")

        elif text == "/newbook" and isAdmin(user.chatId):
            user.status = "uploading_file"
            bot.sendMessage(user.chatId, "📎 Ok, now send me the file for the new ebook.\n"
                                        "Type /cancel to abort.")

        elif text == "/movebook" and isAdmin(user.chatId):
            sent = bot.sendMessage(user.chatId, "📦 Please choose a book from below:")
            bot.editMessageReplyMarkup((user.chatId, sent['message_id']), keyboards.movebook(sent['message_id']))

        elif text == "/syncfiles" and isAdmin(user.chatId):
            syncFiles()
            bot.sendMessage(user.chatId, "♻️ Successfully synced files!")
        
        elif text == "/delbook" and isAdmin(user.chatId):
            sent = bot.sendMessage(user.chatId, "🗑 Please choose a book from below:")
            bot.editMessageReplyMarkup((user.chatId, sent['message_id']), keyboards.delbook(sent['message_id']))

        # General user commands
        elif text == "/start":
            bot.sendMessage(user.chatId, "Hey <b>{}</b>! I'm the Free Books Bot 👋🏻\n"
                                         "I'm currently in <b>Beta Version</b>, but you can already use me to find some books: "
                                         "type /search to find a book by category, or type /help if you have a question.\n"
                                         "I can do only this for the moment, but expect lots of new features in the near future... "
                                         "see you soon!".format(name), parse_mode="HTML")

        elif text == "/help":
            bot.sendMessage(user.chatId, "<b>Help&Commands Page</b>\n"
                                         "Here you can find a list of all the available commands, and more:\n\n"
                                         "/start - Start bot\n"
                                         "/help - Show this page\n"
                                         "/search - Search books by category\n"
                                         "/submit - Send a new ebook for everyone to read\n"
                                         "/cancel - Reset current action", parse_mode="HTML")

        elif text == "/search":
            sent = bot.sendMessage(user.chatId, "🔍 <b>Book Search</b>\n"
                                                "Pick a category from the list below:", parse_mode="HTML")
            bot.editMessageReplyMarkup((user.chatId, sent['message_id']), keyboards.search_cat(sent['message_id']))
        
        elif text == "/submit":
            user.status = "uploading_file"
            bot.sendMessage(user.chatId, "📎 Ok, please send me the new ebook, or type /cancel to abort.\n"
                                        "Supported files: pdf, epub")

        elif text == "/cancel":
            bot.sendMessage(user.chatId, "Operation cancelled!\n"
                                         "I was doing nothing, by the way... 😴")
        
        elif text.startswith("/start getbook"):
            book_id = int(text.split('_')[1])
            book = Book.get(id=book_id)
            with open('ebooks/{}'.format(book.name), 'rb') as upload:
                bot.sendDocument(user.chatId, upload, caption="<b>Book Name:</b> {}\n<b>Category:</b> {}".format(book.name, book.category.name),
                                parse_mode="HTML")

        # Unknown command
        else:
            bot.sendMessage(user.chatId, "😕 Sorry, I didn't understand.\nAre you lost? Type /help")


@db_session
def reply_file(bot, user, msg):
    if user.status != "uploading_file":
        bot.sendMessage(user.chatId, "📕 Sorry, you're currently not uploading a file.\n"
                                     "If you are an authorized admin, type /newbook. Otherwise, type /submit if you would like to submit a new book.")
        return
    fileId = msg['document']['file_id']
    fileName = msg['document']['file_name']
    try:
        bot.download_file(fileId, 'ebooks/{}'.format(fileName))
    except TelegramError:
        bot.sendMessage(user.chatId, "📕 Error: file size must be lower than <b>20MB</b>.", parse_mode="HTML")
        return
    if not Book.exists(lambda b: b.name == fileName):
        book = Book(name=fileName)
        commit()
        if isAdmin(user.chatId):
            user.status = "selecting_category#{}".format(book.id)
            if not select(c for c in Category if c.category != "General")[:]:
                bot.sendMessage(user.chatId, "📗 <b>{}</b> successfully uploaded!\n"
                                            "Please type a name to create a new category:".format(fileName), parse_mode="HTML")
            else:
                sent = bot.sendMessage(user.chatId, "📗 <b>{}</b> successfully uploaded!\n"
                                                    "Please select a category for the book, or type a name to create a new one:".format(fileName), parse_mode="HTML")
                bot.editMessageReplyMarkup((user.chatId, sent['message_id']), keyboards.category(book.id, sent['message_id']))
        else:
            book.category = Category.get(name="General")
            user.status = "normal"
            bot.sendMessage(user.chatId, "📗 <b>{}</b> successfully uploaded!", parse_mode="HTML")
    else:
        bot.sendMessage(user.chatId, "📙 Warning: <b>{}</b> already exists! If you think this is an error, please change the "
                                     "ebook name and reupload it.".format(fileName), parse_mode="HTML")


@db_session
def reply_button(bot, user, query):
    query_split = query.split("#")
    text = query_split[0]
    message_id = int(query_split[1])

    if text.startswith("selcat"):
        text_split = text.split('_')
        cat_id = int(text_split[1])
        book_id = int(text_split[2])
        book = Book.get(id=book_id)
        book.category = Category.get(id=cat_id)
        user.status = "normal"
        bot.editMessageText((user.chatId, message_id), "🗂 Successfully moved book <b>{}</b> to category <i>{}</i>!".format(book.name, book.category.name),
                            parse_mode="HTML", reply_markup=None)

    elif text.startswith("mvbook"):
        book_id = int(text.split('_')[1])
        user.status = "selecting_category#{}".format(book_id)
        bot.editMessageText((user.chatId, message_id), "Please select a category for the book, or type a name to create a new one:",
                            reply_markup=keyboards.category(book_id, message_id))
    
    elif text.startswith("delbook"):
        from os import remove
        book_id = int(text.split('_')[1])
        book = Book.get(id=book_id)
        name = book.name
        remove('ebooks/{}'.format(name))
        book.delete()
        bot.editMessageText((user.chatId, message_id), "🗑 {} successfully deleted.".format(name), reply_markup=None)

    elif text.startswith("searchcat"):
        cat_id = int(text.split('_')[1])
        cat = Category.get(id=cat_id)
        res = ""
        for b in cat.books:
            res += "\n📖 <a href=\"https://t.me/freebooksbbot?start=getbook_{}\">{}</a>".format(b.id, b.name)
        bot.editMessageText((user.chatId, message_id), "🔍 <b>Category: {}</b>\n"
                                                       "Click on any book title, then click on \"Start\" at the bottom to "
                                                       "download the ebook:\n{}".format(cat.name, res),
                            parse_mode="HTML", reply_markup=keyboards.back_search(message_id), disable_web_page_preview=True)

    elif text == "backsearch":
        bot.editMessageText((user.chatId, message_id), "🔍 <b>Book Search</b>\n"
                                                       "Pick a category from the list below:",
                            parse_mode="HTML", reply_markup=keyboards.search_cat(message_id))

    elif text == "moveall":
        bot.editMessageReplyMarkup((user.chatId, message_id), keyboards.movebook(message_id, show_all=True))
    
    elif text == "delall":
        bot.editMessageReplyMarkup((user.chatId, message_id), keyboards.delbook(message_id, show_all=True))
