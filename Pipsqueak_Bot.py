import telegram
import psycopg2
import pytz
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, filters

DATABASE_URL = 'postgres://oylxidwhboayxg:abdc45f4642fa9f329bef28f8e31f967c91d64c1dae3eab5d30e7b6fb62096be@ec2-174-129-32-37.compute-1.amazonaws.com:5432/d52lcq3tkapjck'
TOKEN = '666724238:AAF2SyvjZbui0VMbPOlG3op2jgMQFVFM_yg'
PORT = int(os.environ.get('PORT', '5000'))
BOT = telegram.Bot(token=TOKEN)
BOT.setWebhook(url='https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)


def start(bot, update):
    user_id = update.message.from_user.id
    msg = 'Hello, world!'
    bot.send_message(user_id, msg)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()