import telegram
import psycopg2
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, filters

DATABASE_URL = 'postgres://oylxidwhboayxg:abdc45f4642fa9f329bef28f8e31f967c91d64c1dae3eab5d30e7b6fb62096be@ec2-174-129-32-37.compute-1.amazonaws.com:5432/d52lcq3tkapjck'
TOKEN = '666724238:AAF2SyvjZbui0VMbPOlG3op2jgMQFVFM_yg'
PORT = int(os.environ.get('PORT', '5000'))
BOT = telegram.Bot(token=TOKEN)
BOT.setWebhook(url='https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)


class Database(object):

    def __init__(self):
        os.environ['DATABASE_URL'] = DATABASE_URL
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cur = self.conn.cursor()
        stmt = "CREATE TABLE IF NOT EXISTS ps_database (user_id BIGINT NOT NULL, name TEXT NOT NULL, state TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_user(self, user_id, name):
        stmt = "INSERT INTO ps_database (user_id, name, state) VALUES (%d, '%s', 'home')" % (user_id, name)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_users(self):
        stmt = "SELECT user_id FROM ps_database"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return [x[0] for x in rows]


def start(bot, update):
    global db
    user_id = update.message.from_user.id
    users_list = db.get_users()
    if user_id not in users_list:
        name = update.message.from_user.first_name + ' ' + update.message.from_user.last_name
        db.add_new_user(user_id, name)
    msg = 'Hello, world!'
    bot.send_message(user_id, msg)


def feedback(bot, update):
    admin_id = 111914928
    sender_id = update.message.from_user.id
    message_id = update.message.id
    bot.forward_message(admin_id, sender_id, message_id)


def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))

    dispatcher.add_handler(MessageHandler(filters.Filters.all, feedback))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    main()
