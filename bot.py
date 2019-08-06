from time import sleep
from telepot import Bot
from threading import Thread
from pony.orm import db_session
from modules.database import User
from modules.reply import reply_text, reply_file
from modules.helpers import supportedFile

with open('token.txt', 'r') as f:
    token = f.readline().strip()
    bot = Bot(token)


@db_session
def reply(msg):
    chatId = msg['chat']['id']
    if not User.exists(lambda u: u.chatId == chatId):
        User(chatId=chatId)
    user = User.get(chatId=chatId)
    
    if msg.get('text'):
        reply_text(bot, user, msg)
    
    elif msg.get('document') and supportedFile(msg):
        reply_file(bot, user, msg)
    
    else:
        bot.sendMessage(chatId, "I'm sorry, but this is not a supported file type...\n"
                                "Are you lost? Press /help")


def incoming_message(msg):
    Thread(target=reply, args=[msg]).start()


bot.message_loop({'chat': incoming_message})
while True:
    sleep(60)
