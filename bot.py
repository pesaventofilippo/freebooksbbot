from time import sleep
from telepot import Bot
from threading import Thread
from pony.orm import db_session, select
from telepot.exception import TelegramError, BotWasBlockedError
from modules.database import User

with open('token.txt', 'r') as f:
    token = f.readline().strip()
    bot = Bot(token)

botAdmins = [368894926]


@db_session
def reply(msg):
    chatId = msg['chat']['id']
    text = msg['text']
    name = msg['from']['first_name']

    if not User.exists(lambda u: u.chatId == chatId):
        User(chatId=chatId)
    user = User.get(chatId=chatId)

    if text == "/start":
        bot.sendMessage(chatId, "Hey <b>{}</b>! I'm the Free Books Bot, nice to meet you 👋🏻\n"
                                "I'm sorry, but I'm still under development and as of now I can only greet you... but not for much! "
                                "You can leave this chat open (do not delete that from Telegram, if you want you can 'archive' it) "
                                "and you will be notified as soon as I'm ready to send you some free books to read 😊\n"
                                "Hope to see you soon!".format(name), parse_mode="HTML")

    elif text == "/getusers" and chatId in botAdmins:
        users = select(u for u in User)[:].__len__()
        bot.sendMessage(chatId, "There currently are <b>{}</b> registered users.".format(users), parse_mode="HTML")


def incoming_message(msg):
    Thread(target=reply, args=[msg]).start()


bot.message_loop({'chat': incoming_message})
while True:
    sleep(60)
