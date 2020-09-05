from time import sleep
from telepot import Bot, glance
from threading import Thread
from pony.orm import select, db_session, commit
from modules.database import User, Book, Category
from modules.helpers import supportedFile, isAdmin
from modules import keyboards

with open('token.txt', 'r') as f:
    token = f.readline().strip()
    bot = Bot(token)


@db_session
def reply(msg):
    chatId = msg['chat']['id']
    name = msg['from']['first_name']

    if "text" in msg:
        text = msg['text']
    elif "caption" in msg:
        text = msg['caption']
    else:
        text = ""

    if not User.exists(lambda u: u.chatId == chatId):
        User(chatId=chatId)
    user = User.get(chatId=chatId)

    ## Text Message
    if msg.get('text'):
        if user.status == "uploading_file":
            if text == "/cancel":
                user.status = "normal"
                bot.sendMessage(chatId, "📕 File upload cancelled.")
            else:
                bot.sendMessage(chatId, "❓ Please upload an ebook file.\n"
                                        "Type /cancel to abort.")

        elif user.status.startswith("selecting_category"):
            book_id = int(user.status.split('#', 1)[1])
            book = Book.get(id=book_id)
            if text == "/cancel":
                book.category = Category.get(name="General")
                user.status = "normal"
                bot.sendMessage(chatId, "📗 Book moved to category <b>General</b>.", parse_mode="HTML")
                return

            categories = [cat.name.lower() for cat in select(c for c in Category)[:]]
            if text.lower() not in categories:
                cat = Category(name=text)
                commit()
                book.category = cat
                user.status = "normal"
                bot.sendMessage(chatId, "📗 New category <b>{}</b> successfully added!\n"
                                        "I also added the book to the new category for you.".format(text), parse_mode="HTML")
            else:
                bot.sendMessage(chatId, "📙 Category <b>{}</b> already exists!\n"
                                        "Try with a different name, or select one from the list above.".format(text), parse_mode="HTML")

        elif text == "/users" and isAdmin(chatId):
            users = len(select(u for u in User)[:])
            bot.sendMessage(chatId, "👥 There currently are <b>{}</b> registered users.".format(users), parse_mode="HTML")

        elif text == "/movebook" and isAdmin(chatId):
            sent = bot.sendMessage(chatId, "📦 Please choose the book you want to move:")
            bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.movebook(sent['message_id']))

        elif text == "/delbook" and isAdmin(chatId):
            sent = bot.sendMessage(chatId, "🗑 Please choose the book to delete:")
            bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.delbook(sent['message_id']))

        # General user commands
        elif text == "/start":
            bot.sendMessage(chatId, "Hey <b>{}</b>! I'm the Free Books Bot 👋🏻\n"
                                    "I'm currently in <b>Beta Version</b>, but you can already use me to find some books: "
                                    "type /search to find a book by category, or type /help if you have any question."
                                    "".format(name), parse_mode="HTML")

        elif text == "/help":
            bot.sendMessage(chatId, "<b>Commands List</b>\n\n"
                                    "/start - Start bot\n"
                                    "/help - Show this page\n"
                                    "/search - Search books by category\n"
                                    "/submit - Send a new ebook for everyone to read\n"
                                    "/cancel - Reset current action", parse_mode="HTML")

        elif text == "/search":
            sent = bot.sendMessage(chatId, "🔍 <b>Book Search</b>\n"
                                           "Pick a category from the list below:", parse_mode="HTML")
            bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.search_cat(sent['message_id']))

        elif text == "/submit":
            user.status = "uploading_file"
            bot.sendMessage(chatId, "📎 Ok, please send me the new ebook, or type /cancel to abort.\n"
                                    "<i>Only PDF files are supported.</i>", parse_mode="HTML")

        elif text == "/cancel":
            bot.sendMessage(chatId, "Operation cancelled!\n"
                                    "I was doing nothing, by the way... 😴")

        elif text.startswith("/start getbook"):
            book_id = int(text.split('_')[1])
            book = Book.get(id=book_id)
            bot.sendDocument(chatId, book.telegramFileId,
                             f"<b>Book Name:</b> {book.name}\n"
                             f"<b>Category:</b> {book.category.name}", "HTML")

        # Unknown command
        else:
            bot.sendMessage(chatId, "😕 Sorry, I didn't understand.\n"
                                    "Need /help?")


    ## File Document
    elif msg.get('document') and supportedFile(msg):
        if user.status != "uploading_file":
            bot.sendMessage(chatId, "📕 Sorry, you're currently not uploading a file.\n"
                                    "Type /submit if you would like to submit a new book.")
            return

        fileId = msg['document']['file_id']
        fileSize = msg['document']['file_size']
        fileName = msg['document']['file_name']
        if fileSize > 50000000: # 50MB Telegram Limit (in bytes)
            bot.sendMessage(chatId, "📕 Error: file size must be lower than <b>50MB</b>.", parse_mode="HTML")
            return

        if not Book.exists(lambda b: b.name == fileName):
            book = Book(name=fileName, telegramFileId=fileId)
            commit()
            if isAdmin(chatId):
                user.status = "selecting_category#{}".format(book.id)
                if not select(c for c in Category if c.name != "General")[:]:
                    bot.sendMessage(chatId, "📗 <b>{}</b> successfully uploaded!\n"
                                            "Please type a name to create a new category:".format(fileName), parse_mode="HTML")
                else:
                    sent = bot.sendMessage(chatId, "📗 <b>{}</b> successfully uploaded!\n"
                                                   "Please select a category for the book, or type a name to create a new one:"
                                                   "".format(fileName), parse_mode="HTML")
                    bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.category(book.id, sent['message_id']))
            else:
                book.category = Category.get(name="General")
                user.status = "normal"
                bot.sendMessage(chatId, "📗 <b>{}</b> successfully uploaded!", parse_mode="HTML")

        # Book with same name already exists
        else:
            bot.sendMessage(chatId, "📙 Warning: \"<b>{}</b>\" already exists! If you think this is an error, please "
                                    "change the file name and reupload it.".format(fileName), parse_mode="HTML")

    # Filetype not supported
    else:
        bot.sendMessage(chatId, "🤨 I'm sorry, but this is not a supported file type...\n"
                                "Are you lost? Press /help")


@db_session
def button(msg):
    chatId, query_data = glance(msg, flavor="callback_query")[1:3]
    user = User.get(chatId=chatId)
    query_split = query_data.split("#")
    text = query_split[0]
    message_id = int(query_split[1])

    if text.startswith("selcat"):
        text_split = text.split('_')
        book = Book.get(id=int(text_split[2]))
        book.category = Category.get(id=int(text_split[1]))
        user.status = "normal"
        bot.editMessageText((chatId, message_id), "🗂 Successfully moved book <b>{}</b> to category <b>{}</b>!".format(
            book.name, book.category.name), parse_mode="HTML", reply_markup=None)

    elif text.startswith("mvbook"):
        book_id = int(text.split('_')[1])
        user.status = "selecting_category#{}".format(book_id)
        bot.editMessageText((chatId, message_id), "Please select a category for the book, or type a name to create a new one:",
                            reply_markup=keyboards.category(book_id, message_id))

    elif text.startswith("delbook"):
        book_id = int(text.split('_')[1])
        book = Book.get(id=book_id)
        name = book.name
        book.delete()
        bot.editMessageText((chatId, message_id), "🗑 <b>{}</b> successfully deleted.".format(name), parse_mode="HTML", reply_markup=None)

    elif text.startswith("searchcat"):
        cat_id = int(text.split('_')[1])
        cat = Category.get(id=cat_id)
        res = ""
        for b in cat.books:
            res += "\n📖 <a href=\"https://t.me/freebooksbbot?start=getbook_{}\">{}</a>".format(b.id, b.name)
        bot.editMessageText((chatId, message_id), "🔍 <b>Category: {}</b>\n"
                                                  "Click on any book title, then click on \"Start\" at the bottom to "
                                                  "download the ebook:\n\n"
                                                  "{}".format(cat.name, res), parse_mode="HTML",
                            reply_markup=keyboards.back_search(message_id), disable_web_page_preview=True)

    elif text == "backsearch":
        bot.editMessageText((chatId, message_id), "🔍 <b>Book Search</b>\n"
                                                  "Pick a category from the list below:",
                            parse_mode="HTML", reply_markup=keyboards.search_cat(message_id))

    elif text == "moveall":
        bot.editMessageReplyMarkup((chatId, message_id), keyboards.movebook(message_id, show_all=True))

    elif text == "delall":
        bot.editMessageReplyMarkup((chatId, message_id), keyboards.delbook(message_id, show_all=True))


def incoming_message(msg):
    Thread(target=reply, args=[msg]).start()

def incoming_query(msg):
    Thread(target=button, args=[msg]).start()


bot.message_loop({'chat': incoming_message, 'callback_query': incoming_query})
while True:
    sleep(60)
