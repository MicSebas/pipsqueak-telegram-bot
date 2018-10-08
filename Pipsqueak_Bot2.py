import telegram
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from Database import Database

TOKEN = '666724238:AAF2SyvjZbui0VMbPOlG3op2jgMQFVFM_yg'
PORT = int(os.environ.get('PORT', '5000'))
BOT = telegram.Bot(token=TOKEN)
BOT.setWebhook(url='https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)


def pre_check(user_id, name, state='home'):
    global db
    users_list = db.get_users()
    if user_id not in users_list:
        db.add_new_user(user_id, name, state)
        return state
    else:
        return db.get_state(user_id)


# Commands
def start(bot, update):
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state == 'home':
        msg = 'Hello, %s! Welcome to Pipsqueak, the marketplace by SUTD students for SUTD students!\n\nYou can /buy, /sell, and /browse spare parts and other items.' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first.'
        bot.send_message(user_id, msg)


def done(bot, update):
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state.startswith('sell') or state.startswith('buy'):
        msg = 'You are in the middle of a transaction. Please use /cancel if you want to cancel the transaction.'
        bot.send_message(user_id, msg)
    elif state != 'home':
        global db
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    else:
        msg = 'You\'re not in the middle of any operation. Say /start to begin trading now!'
        bot.send_message(user_id, msg)


def force_cancel(bot, update):
    global db
    user_id = update.message.from_user.id
    db.update_state(user_id, 'home')
    msg = 'Back to home state'
    bot.send_message(user_id, msg)


def browse(bot, update):
    user_id = update.message.from_user.id
    pre_check(user_id, update.message.from_user.name)
    filename = 'Pipsqueak_catalog.csv'
    f = open(filename, 'w')
    f.write('Date Listed, Item ID, Category, Item, Description, Price\n')
    items = db.get_items_list()
    for item in items:
        f.write('%s, %s, %s, %s, %s, $%.2f\n' % item)
    f.close()
    msg = 'Here are the items currently listed at Pipsqueak!'
    bot.send_document(user_id, open(filename, 'rb'), caption=msg)


def sell_command(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name, 'sell')
    if state != 'home' and state != 'sell':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first.'
        bot.send_message(user_id, msg)
    else:
        if state == 'home':
            db.update_state(user_id, 'sell')
        msg = 'What kind of item are you selling?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Electronics', callback_data='Electronics')],
                                         [InlineKeyboardButton('Stationery', callback_data='Stationery')],
                                         [InlineKeyboardButton('Materials', callback_data='Materials')],
                                         [InlineKeyboardButton('Adhesives', callback_data='Adhesives')],
                                         [InlineKeyboardButton('Paints', callback_data='Paints')],
                                         [InlineKeyboardButton('Consumables', callback_data='Consumables')],
                                         [InlineKeyboardButton('Others', callback_data='Others')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)


def buy_command(bot, update):
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name, 'buy')
    if state != 'home' and state != 'buy':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first.'
        bot.send_message(user_id, msg)
    else:
        if state == 'home':
            db.update_state(user_id, 'buy')
        msg = 'What kind of item are you selling?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Electronics', callback_data='Electronics')],
                                         [InlineKeyboardButton('Stationery', callback_data='Stationery')],
                                         [InlineKeyboardButton('Materials', callback_data='Materials')],
                                         [InlineKeyboardButton('Adhesives', callback_data='Adhesives')],
                                         [InlineKeyboardButton('Paints', callback_data='Paints')],
                                         [InlineKeyboardButton('Consumables', callback_data='Consumables')],
                                         [InlineKeyboardButton('Others', callback_data='Others')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)


# Callback Query Handlers
def callback_query_handler(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    state = db.get_state(user_id)
    data = update.callback_query.data
    msg_id = update.callback_query.message.message_id
    if state == 'sell':
        if data != 'Others':
            item_id = db.add_new_item(data, user_id)
            db.update_state(user_id, 'sell_%s_name' % item_id)
            msg = 'Selling %s.\nWhat item are you selling?' % data.lower()
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        else:
            db.update_state(user_id, 'sell_Others')
            msg = 'You requested to sell an item which we may not prepared to host.\n\nBefore proceeding, please note that your request may be moderated and subject to approval. Do you want to continue?'
            # keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data=True)],
            #                                  [InlineKeyboardButton('No', callback_data=False)]])
            keyboard = [[{'text': 'Yes', 'callback_data': True}, {'text': 'No', 'callback_data': False}]]
            print('editing message')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            # bot.edit_message_reply_markup(user_id, msg_id, reply_markup=keyboard)
    elif state == 'sell_Others':
        if data:
            db.update_state(user_id, 'sell_Others_request')
            msg = 'You requested for approval to sell an item. What item do you want to sell?'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        else:
            db.update_state(user_id, 'home')
            msg = 'You cancelled the operation. Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.message.from_user.first_name
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif update.callback_query.message.text.startswith('Request: '):
        if data[0]:
            user_id = data[1]
            item = data[2]
            item_id = db.add_new_item('Others', user_id)
            db.update_item(item_id, 'name', item)
            db.update_state(user_id, 'sell_%s_description' % item_id)
            msg = 'Admin has APPROVED your request to sell the following item: %s.\n\nPlease send a short description to help potential buyers.' % item
            bot.send_message(user_id, msg)
        else:
            user_id = data[1]
            item = data[2]
            msg = 'Admin has unfortunately rejected your request to sell the following item: %s. We have to filter the items that we provide to ensure they follow our company and community guidelines. We hope to see you again soon!' % item
            bot.send_message(user_id, msg)
    else:
        msg = 'Please use /start to begin trading!'
        bot.send_message(user_id, msg)


# Message Handlers
def message_handler(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state == 'sell_Others_request':
        text = update.message.text
        admin_id = 111914928
        msg = 'Request: %s (%d) has requested to sell the following item: %s.\n\nDo you approve of this listing?' % (update.message.from_user.name, user_id, text)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data=(True, user_id, text)), InlineKeyboardButton('No', callback_data=(False, user_id, text))]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif state.startswith('sell_') and not state.startswith('sell_Others'):
        [_, item_id, column] = state.split('_')
        text = update.message.text
        db.update_item(item_id, column, text)
        if column == 'name':
            db.update_state(user_id, 'sell_%s_description' % item_id)
            msg = 'Please send a short description of your item to help potential buyers.'
            bot.send_message(user_id, msg)
        elif column == 'description':
            db.update_state(user_id, 'sell_%s_price' % item_id)
            msg = 'How much are you selling this item for?'
            bot.send_message(user_id, msg)
        else:
            db.update_state(user_id, 'home')
            msg = 'Thank you for using Pipsqueak, %s! We will inform you as soon as someone offers to buy your item! We hope to see you soon!' % update.message.from_user.first_name
            bot.send_message(user_id, msg)
    else:
        msg = 'Please use /start to begin trading!'
        bot.send_message(user_id, msg)


def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('done', done))
    dispatcher.add_handler(CommandHandler('browse', browse))
    dispatcher.add_handler(CommandHandler('sell', sell_command))
    dispatcher.add_handler(CommandHandler('force_cancel', force_cancel))

    dispatcher.add_handler(MessageHandler(filters.Filters.all, message_handler))

    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    main()