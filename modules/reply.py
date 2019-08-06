from modules.helpers import isAdmin, getFileType
from modules.database import User, Book
from pony.orm import select


def reply_text(bot, user, msg):
    name = msg['from']['first_name']
    text = msg['text']

    if user.status == "uploading_file":
        if text == "/cancel":
            user.status = "normal"
            bot.sendMessage(user.chatId, "File Upload cancelled.")
        
        else:
            bot.sendMessage(user.chatId, "Please upload an ebook file. Type /cancel to abort.")
    
    elif user.status == "normal":
        if text == "/start":
            bot.sendMessage(user.chatId, "Hey <b>{}</b>! I'm the Free Books Bot, nice to meet you 👋🏻\n"
                                         "I'm sorry, but I'm still under development and as of now I can only greet you... but not for much! "
                                         "You can leave this chat open (do not delete that from Telegram, if you want you can 'archive' it) "
                                         "and you will be notified as soon as I'm ready to send you some free books to read 😊\n"
                                         "Hope to see you soon!".format(name), parse_mode="HTML")

        elif text == "/getusers" and isAdmin(user.chatId):
            users = select(u for u in User)[:].__len__()
            bot.sendMessage(user.chatId, "There currently are <b>{}</b> registered users.".format(users), parse_mode="HTML")
        
        elif text == "/newbook" and isAdmin(user.chatId):
            user.status = "uploading_file"
            bot.sendMessage(user.chatId, "Ok, now send me the file for the new ebook.\n"
                                         "Type /cancel to abort.")
        
        elif text == "/cancel":
            bot.sendMessage(user.chatId, "Operation cancelled!\n"
                                         "I was doing nothing, by the way...")


def reply_file(bot, user, msg):
    if user.status != "uploading_file":
        bot.sendMessage(user.chatId, "Sorry, you're currently not uploading a file.\n"
                                     "If you are an authorized admin, type /newbook.")
        return
    file = msg['document']
    fileId = file['file_id']
    fileName = file['file_name']
    bot.download_file(fileId, 'ebooks/{}'.format(fileName))
    if not Book.exists(lambda b: b.name == fileName):
        Book(fileId=fileId, name=fileName)
        user.status = "normal"
        bot.sendMessage(user.chatId, "{} successfully uploaded!".format(fileName))
    else:
        bot.sendMessage(user.chatId, "Warning: {} already exists! If you think this is an error, please change the "
                                     "ebook name and reupload it.".format(fileName))
