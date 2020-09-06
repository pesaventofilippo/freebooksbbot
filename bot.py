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

    if not Category.exists(lambda c: c.name == "General"):
        Category(name= "General")
    if not User.exists(lambda u: u.chatId == chatId):
        User(chatId=chatId)
    user = User.get(chatId=chatId)

    ## Text Message
    if msg.get('text'):
        if user.status.endswith("uploading_file"):
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
                bot.sendMessage(chatId, f"📗 New category <b>{text}</b> successfully added!\n"
                                        f"I also added the book to the new category for you.", parse_mode="HTML")
            else:
                bot.sendMessage(chatId, f"📙 Category <b>{text}</b> already exists!\n"
                                        f"Try with a different name, or select one from the list above.", parse_mode="HTML")

        elif text == "/getusers" and isAdmin(chatId):
            users = len(select(u for u in User)[:])
            bot.sendMessage(chatId, f"👥 There currently are <b>{users}</b> registered users.", parse_mode="HTML")

        elif text == "/getbooks" and isAdmin(chatId):
            books = len(select(b for b in Book)[:])
            bot.sendMessage(chatId, f"📚 There currently are <b>{books}</b> books.", parse_mode="HTML")

        elif text == "/movebook" and isAdmin(chatId):
            sent = bot.sendMessage(chatId, "📦 Please choose the book you want to move:")
            bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.manageBooks("move", sent['message_id']))

        elif text == "/delbook" and isAdmin(chatId):
            sent = bot.sendMessage(chatId, "🗑 Please choose the book to delete:")
            bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.manageBooks("del", sent['message_id']))

        elif text == "/bulkupload":
            user.status = "bulk_uploading_file"
            bot.sendMessage(chatId, "📎 <b>Bulk Upload mode active.</b> Type /cancel to abort.\n"
                                    "<i>Only PDF files are supported.</i>", parse_mode="HTML")

        # General user commands
        elif text == "/start":
            bot.sendMessage(chatId, f"Hey <b>{name}</b>! I'm the Free Books Bot 👋🏻\n"
                                    f"I'm currently in <b>Beta Version</b>, but you can already use me to find some books: "
                                    f"type /search to find a book by category, or type /help if you have any question.",
                            parse_mode="HTML")

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
        if not user.status.endswith("uploading_file"):
            bot.sendMessage(chatId, "📕 Sorry, you're currently not uploading a file.\n"
                                    "Type /submit if you would like to submit a new book.")
            return

        fileId = msg['document']['file_id']
        fileSize = msg['document']['file_size']
        fileName = msg['document']['file_name']
        if fileSize > 50000000: # 50MB Telegram Limit (in bytes)
            bot.sendMessage(chatId, "📕 Sorry, the file size must be lower than <b>50MB</b>.", parse_mode="HTML")
            return

        if not Book.exists(lambda b: b.name == fileName):
            book = Book(name=fileName, telegramFileId=fileId)
            commit()

            if (not isAdmin(chatId)) or (user.status == "bulk_uploading_file"):
                book.category = Category.get(name="General")
                if user.status != "bulk_uploading_file":
                    user.status = "normal"
                bot.sendMessage(chatId, f"📗 <b>{fileName}</b> successfully uploaded!", parse_mode="HTML")

            else:
                user.status = f"selecting_category#{book.id}"
                if not select(c for c in Category if c.name != "General")[:]:
                    bot.sendMessage(chatId, f"📗 <b>{fileName}</b> successfully uploaded!\n"
                                            f"Please type a name to create a new category:", parse_mode="HTML")
                else:
                    sent = bot.sendMessage(chatId, f"📗 <b>{fileName}</b> successfully uploaded!\n"
                                                   f"Please select a category for the book, or type a name to create a new one:",
                                           parse_mode="HTML")
                    bot.editMessageReplyMarkup((chatId, sent['message_id']), keyboards.category(book.id, sent['message_id']))

        # Book with same name already exists
        else:
            bot.sendMessage(chatId, f"📙 Warning: \"<b>{fileName}</b>\" already exists! If you think this is an error, please "
                                    f"change the file name and reupload it.", parse_mode="HTML")

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
        bot.editMessageText((chatId, message_id), f"🗂 Successfully moved book <b>{book.name}</b> to category "
                                                  f"<b>{book.category.name}</b>!", parse_mode="HTML", reply_markup=None)

    elif text.startswith("movebook"):
        book_id = int(text.split('_')[1])
        user.status = f"selecting_category#{book_id}"
        bot.editMessageText((chatId, message_id), "Please select a category for the book, or type a name to create a new one:",
                            reply_markup=keyboards.category(book_id, message_id))

    elif text.startswith("delbook"):
        book_id = int(text.split('_')[1])
        book = Book.get(id=book_id)
        name = book.name
        book.delete()
        bot.editMessageText((chatId, message_id), f"🗑 <b>{name}</b> successfully deleted.", parse_mode="HTML", reply_markup=None)

    elif text.startswith("searchcat"):
        cat_id = int(text.split('_')[1])
        cat = Category.get(id=cat_id)
        res = ""
        for b in sorted(cat.books, key=lambda x: x.name):
            res += f"\n📖 <a href=\"https://t.me/freebooksbbot?start=getbook_{b.id}\">{b.name}</a>"
        bot.editMessageText((chatId, message_id), f"🔍 <b>Category: {cat.name}</b>\n"
                                                  f"Click on any book title, then click on \"Start\" at the bottom to "
                                                  f"download the ebook:\n" + res, parse_mode="HTML",
                            reply_markup=keyboards.back_search(message_id), disable_web_page_preview=True)

    elif text == "backsearch":
        bot.editMessageText((chatId, message_id), "🔍 <b>Book Search</b>\n"
                                                  "Pick a category from the list below:",
                            parse_mode="HTML", reply_markup=keyboards.search_cat(message_id))

    elif text == "moveall":
        bot.editMessageReplyMarkup((chatId, message_id), keyboards.manageBooks("move", message_id, show_all=True))

    elif text == "delall":
        bot.editMessageReplyMarkup((chatId, message_id), keyboards.manageBooks("del", message_id, show_all=True))


def incoming_message(msg):
    Thread(target=reply, args=[msg]).start()

def incoming_query(msg):
    Thread(target=button, args=[msg]).start()


bot.message_loop({'chat': incoming_message, 'callback_query': incoming_query})
while True:
    sleep(60)
