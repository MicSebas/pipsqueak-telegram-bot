import telegram
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from Database import Database

TOKEN = '666724238:AAF2SyvjZbui0VMbPOlG3op2jgMQFVFM_yg'
PORT = int(os.environ.get('PORT', '5000'))
BOT = telegram.Bot(token=TOKEN)
BOT.setWebhook(url='https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)


# Commands
def start(bot, update):
    global db
    user_id = update.message.from_user.id
    users_list = db.get_users()
    if user_id not in users_list:
        name = update.message.from_user.first_name + ' ' + update.message.from_user.last_name
        db.add_new_user(user_id, name)
    msg = 'Hello, world!'
    bot.send_message(user_id, msg)


def done(bot, update):
    global db
    user_id = update.message.from_user.id
    state = db.get_state(user_id)
    if state != 'home':
        msg = 'Thank you for using Pipsqueak! We look forward to your next visit, %s!' % update.message.from_user.first_name
        db.update_state(user_id, 'home')
    else:
        msg = 'You\'re not in the middle of any operation.'
    bot.send_message(user_id, msg)


def send_feedback(bot, update):
    global db
    user_id = update.message.from_user.id
    db.update_state(user_id, 'feedback')
    msg = 'You can send in your feedback to me now!'
    bot.send_message(user_id, msg)


def browse_listings(bot, update):
    global db
    user_id = update.message.from_user.id
    items = db.get_items()
    file_name = 'Pipsqueak SUTD Listing.csv'
    f = open(file_name, 'w')
    f.write('Item ID, Item Name, Description, Condition, Price\n')
    for item in items:
        f.write('%s, %s, %s, %s, %s, %.2f\n' % item)
    f.close()
    msg = 'Here are the items currently listed!'
    bot.send_message(user_id, msg)
    bot.send_document(user_id, open(file_name, 'rb'))


def admin_reply_command(bot, update):
    global db
    user_id = update.message.from_user.id
    db.update_state(user_id, 'admin_reply')
    msg = 'Send me the user ID of the person you want to reply to.'
    bot.send_message(user_id, msg)


def sell_command(bot, update):
    global db
    user_id = update.message.from_user.id
    db.update_state(user_id, 'sell')
    msg = 'What kind of item are you selling?'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Tools', callback_data='T')],
                                     [InlineKeyboardButton('Materials', callback_data='M')],
                                     [InlineKeyboardButton('Electronics', callback_data='E')],
                                     [InlineKeyboardButton('Mechanical Parts', callback_data='P')],
                                     [InlineKeyboardButton('Others', callback_data='O')]])
    bot.send_message(user_id, msg, reply_markup=keyboard)


# Message handlers
def feedback(bot, update):
    admin_id = 111914928
    sender_id = update.message.from_user.id
    sender_name = update.message.from_user.first_name + ' ' + update.message.from_user.last_name
    message_id = update.message.message_id
    msg = '%s (%d) said:' % (sender_name, sender_id)
    bot.send_message(admin_id, msg)
    bot.forward_message(admin_id, sender_id, message_id)
    msg = 'Thank you for your feedback! Anything else you want to say?\nSend /done if you\'re finished with your feedback!'
    bot.send_message(sender_id, msg)


def admin_reply(bot, update, target_id):
    msg = update.message.text
    bot.send_message(target_id, msg)
    admin_id = update.message.from_user.id
    msg = 'Forwarded! Anything else you want to say?\nSend /done if you\'re finished with your reply!'
    bot.send_message(admin_id, msg)


def message_handler(bot, update):
    global db
    user_id = update.message.from_user.id
    state = db.get_state(user_id)
    if state == 'feedback':
        feedback(bot, update)
    elif state == 'admin_reply':
        db.update_state(user_id, state + '_%s' % update.message.text)
        msg = 'You can send your reply now! I will forward it to your recipient.'
        bot.send_message(user_id, msg)
    elif state.startswith('admin_reply_'):
        target_id = int(state[12:])
        admin_reply(bot, update, target_id)


# Main
def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('done', done))
    dispatcher.add_handler(CommandHandler('feedback', send_feedback))
    dispatcher.add_handler(CommandHandler('admin_reply', admin_reply_command))
    dispatcher.add_handler(CommandHandler('browse_listings', browse_listings))
    dispatcher.add_handler(CommandHandler('sell', sell_command))

    dispatcher.add_handler(MessageHandler(filters.Filters.all, message_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    main()
