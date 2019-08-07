from modules.helpers import isAdmin, getFileType
from modules.database import User, Book, Category
from modules import keyboards
from pony.orm import select, db_session, commit


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
        categories = [cat.name.lower() for cat in select(c for c in Category)[:]]
        book = Book.get(id=int(user.status.split('#', 1)[1]))
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
        if text == "/start":
            bot.sendMessage(user.chatId, "Hey <b>{}</b>! I'm the Free Books Bot, nice to meet you 👋🏻\n"
                                         "I'm sorry, but I'm still under development and as of now I can only greet you... but not for much! "
                                         "You can leave this chat open (do not delete that from Telegram, if you want you can 'archive' it) "
                                         "and you will be notified as soon as I'm ready to send you some free books to read 😊\n"
                                         "<i>Hope to see you soon!</i>".format(name), parse_mode="HTML")
        
        elif text == "/help":
            bot.sendMessage(user.chatId, "😕 Sorry - I'm still under development. Type /start for more info.")

        elif text == "/getusers" and isAdmin(user.chatId):
            users = select(u for u in User)[:].__len__()
            bot.sendMessage(user.chatId, "👥 There currently are <b>{}</b> registered users.".format(users), parse_mode="HTML")
        
        elif text == "/getbooks" and isAdmin(user.chatId):
            books = [book.name for book in select(b for b in Book)[:]]
            bot.sendMessage(user.chatId, "📚 List of currently registered books:\n"
                                         "- {}".format("\n- ".join(books)))
        
        elif text == "/newbook" and isAdmin(user.chatId):
            user.status = "uploading_file"
            bot.sendMessage(user.chatId, "📎 Ok, now send me the file for the new ebook.\n"
                                         "Type /cancel to abort.")
        
        elif text == "/cancel":
            bot.sendMessage(user.chatId, "Operation cancelled!\n"
                                         "I was doing nothing, by the way... 😴")


@db_session
def reply_file(bot, user, msg):
    if user.status != "uploading_file":
        bot.sendMessage(user.chatId, "📕 Sorry, you're currently not uploading a file.\n"
                                     "If you are an authorized admin, type /newbook.")
        return
    file = msg['document']
    fileId = file['file_id']
    fileName = file['file_name']
    bot.download_file(fileId, 'ebooks/{}'.format(fileName))
    if not Book.exists(lambda b: b.name == fileName):
        book = Book(name=fileName)
        commit()
        user.status = "selecting_category#{}".format(book.id)
        if not select(c for c in Category)[:]:
            bot.sendMessage(user.chatId, "📗 <b>{}</b> successfully uploaded!\n"
                                         "Please type a name to create a new category:".format(fileName), parse_mode="HTML")
        else:
            sent = bot.sendMessage(user.chatId, "📗 <b>{}</b> successfully uploaded!\n"
                                                "Please select a category for the book, or type a name to create a new one:".format(fileName), parse_mode="HTML")
            bot.editMessageReplyMarkup((user.chatId, sent['message_id']), keyboards.category(book.idn, sent['message_id']))
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
        cat_name = text_split[1]
        book_id = int(text_split[2])
        book = Book.get(id=book_id)
        book.category = Category.get(name=cat_name)
        user.status = "normal"
        bot.editMessageText((user.chatId, message_id), "🗂 Successfully moved book <b>{}</b> to category <b>{}</b>!".format(book.name, book.category), parse_mode="HTML", reply_markup=None)
