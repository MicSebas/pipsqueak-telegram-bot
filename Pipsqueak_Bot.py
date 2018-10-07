import telegram
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
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
    msg = 'Hello, %s! Welcome to Pipsqueak SUTD, a marketplace to buy and sell your spare parts!\n\nYou can send /buy, /sell, or /browse to start trading!' % update.message.from_user.first_name
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
    file_name = 'Pipsqueak_SUTD_Listing.csv'
    f = open(file_name, 'w')
    f.write('Item ID, Item Name, Description, Condition, Price\n')
    for item in items:
        f.write('%s, %s, %s, %s, $%.2f\n' % item)
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


# Callback Query Handler
def callback_query_handler(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    state = db.get_state(user_id)
    data = update.callback_query.data
    if state == 'sell':
        user_name = update.callback_query.from_user.first_name + ' ' + update.callback_query.from_user.last_name
        item_code = db.add_new_item(data, user_id, user_name)
        msg = 'What are you selling?'
        new_state = 'sell_%s_name' % item_code
        keyboard = None
    else:
        msg = ''
        new_state = state
        keyboard = None
    db.update_state(user_id, new_state)
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


def sell_details(bot, update, item_code, column):
    global db
    user_id = update.message.from_user.id
    text = update.message.text
    db.update_item(item_code, column, text)
    if column == 'name':
        msg = 'Please send me a short description of the item!'
        new_state = 'sell_%s_description' % item_code
        keyboard = None
    elif column == 'description':
        msg = 'Is the item used or unused?'
        new_state = 'sell_%s_condition' % item_code
        keyboard = ReplyKeyboardMarkup([['Used', 'Unused']], one_time_keyboard=True)
    elif column == 'condition':
        msg = 'How much are you selling this item for?'
        new_state = 'sell_%s_price'
        keyboard = None
    else:
        msg = 'Your item has been listed! We will contact you as soon as you have a buyer!'
        new_state = 'home'
        keyboard = None
    db.update_state(user_id, new_state)
    bot.send_message(user_id, msg, reply_markup=keyboard)
    return new_state


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
    elif state.startswith('sell_'):
        state_list = state.split('_')
        item_code = state_list[1]
        column = state_list[2]
        sell_details(bot, update, item_code, column)


# Main
def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('done', done))
    dispatcher.add_handler(CommandHandler('feedback', send_feedback))
    dispatcher.add_handler(CommandHandler('admin_reply', admin_reply_command))
    dispatcher.add_handler(CommandHandler('browse', browse_listings))
    dispatcher.add_handler(CommandHandler('sell', sell_command))

    dispatcher.add_handler(MessageHandler(filters.Filters.all, message_handler))
    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    main()
