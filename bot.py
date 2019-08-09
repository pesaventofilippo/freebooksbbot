from time import sleep
from telepot import Bot, glance
from threading import Thread
from pony.orm import db_session
from modules.database import User
from modules.reply import reply_text, reply_file, reply_button
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
        bot.sendMessage(chatId, "🤨 I'm sorry, but this is not a supported file type...\n"
                                "Are you lost? Press /help")


@db_session
def button(msg):
    chatId, query_data = glance(msg, flavor="callback_query")[1:3]
    user = User.get(chatId=chatId)
    reply_button(bot, user, query_data)


def incoming_message(msg):
    Thread(target=reply, args=[msg]).start()

def incoming_query(msg):
    Thread(target=button, args=[msg]).start()


bot.message_loop({'chat': incoming_message, 'callback_query': incoming_query})
while True:
    sleep(60)
