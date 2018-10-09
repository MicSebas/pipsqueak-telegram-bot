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
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state.startswith('sell') or state.startswith('buy'):
        msg = 'You are in the middle of a transaction. Please use /cancel if you want to cancel the transaction.'
        bot.send_message(user_id, msg)
    elif state.startswith('forward_'):
        [_, seller_id, seller_name] = state.split('_')
        db.update_state(user_id, 'home')
        msg = 'You are no longer connected to %s' % seller_name
        bot.send_message(user_id, msg)
        db.update_state(int(seller_id), 'home')
        msg = 'You are no longer connected to the admin. Thank you for using Pipsqueak!'
        bot.send_message(int(seller_id), msg)
    elif state == 'feedback':
        global admin_id
        admin_state = db.get_state(admin_id)
        if admin_state.startswith('forward_'):
            msg = 'The admin is still talking to you. It might be important.'
            bot.send_message(user_id, msg)
        else:
            db.update_state(user_id, 'home')
            msg = 'Thank you for your feedback! We are always trying to improve Pipsqueak for you!'
            bot.send_message(user_id, msg)
    elif state != 'home':
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    else:
        msg = 'You\'re not in the middle of any operation. Say /start to begin trading now!'
        bot.send_message(user_id, msg)


def cancel(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state == 'home':
        msg = 'You\'re not in the middle of any operation. Say /start to begin trading now!'
        bot.send_message(user_id, msg)
    elif state == 'sell' or state.startswith('sell_Others'):
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    elif state.startswith('sell_'):
        state_list = state.split('_')
        item_id = state_list[1]
        db.delete_item(item_id)
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    else:
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.message.from_user.first_name
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
        global db
        if state == 'home':
            db.update_state(user_id, 'buy')
        msg = 'What are you buying? You can either type in the item ID or choose from the buttons below.'
        categories = []
        items = db.get_items_list()
        for category in [item[2] for item in items]:
            if category not in categories:
                categories.append(category)
        keyboard = [[InlineKeyboardButton(category, callback_data=category)] for category in categories]
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='None')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.send_message(user_id, msg, reply_markup=keyboard)


def feedback(bot, update):
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first.'
        bot.send_message(user_id, msg)
    else:
        global db
        msg = 'You are now connected to an admin. I will forward everything you say to them.\nUse /done when you\'re finished!'
        db.update_state(user_id, 'feedback')
        bot.send_message(user_id, msg)


# Callback Query Handlers
def callback_query_handler(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    state = db.get_state(user_id)
    data = update.callback_query.data
    msg_id = update.callback_query.message.message_id
    if update.callback_query.message.text.startswith('Request: '):
        data = data.split('_')
        if data[0] == 'True':
            msg = 'Request approved.'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            seller_id = int(data[1])
            item = data[2]
            item_id = db.add_new_item('Others', seller_id)
            db.update_item(item_id, 'name', item)
            db.update_state(seller_id, 'sell_%s_description' % item_id)
            msg = 'Admin has APPROVED your request to sell the following item: %s.\n\nPlease send a short description to help potential buyers.' % item
            bot.send_message(seller_id, msg)
        else:
            msg = 'Request denied.'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            seller_id = int(data[1])
            item = data[2]
            msg = 'Admin has unfortunately rejected your request to sell the following item: %s.\n\nWe have to filter the items that we provide to ensure they follow our company and community guidelines. We hope to see you again soon!' % item
            bot.send_message(seller_id, msg)
    elif update.callback_query.message.text.startswith('Purchase: '):
        [seller_id, seller_name] = data.split('_')
        db.update_state(user_id, 'forward_%d' % seller_id)
        db.update_state(int(seller_id), 'feedback')
        msg = 'You are now connected to %s! Use /done when you\'re finished.' % seller_name
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        msg = 'Congratulations, someone wants to purchase your item! Please wait for an admin to contact you to set up a time to pick up your item.'
        bot.send_message(int(seller_id), msg)
    elif state == 'sell':
        if data != 'Others':
            item_id = db.add_new_item(data, user_id)
            db.update_state(user_id, 'sell_%s_name' % item_id)
            msg = 'Selling %s.\nWhat item are you selling?' % data.lower()
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        else:
            db.update_state(user_id, 'sell_Others')
            msg = 'You requested to sell an item which we may not be prepared to host.\n\nBefore proceeding, please note that your request may be moderated and subject to approval. Do you want to continue?'
            keyboard = [[InlineKeyboardButton('Yes', callback_data='Yes'), InlineKeyboardButton('No', callback_data='No')]]
            keyboard = InlineKeyboardMarkup(keyboard)
            print('editing message')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif state == 'sell_Others':
        if data == 'Yes':
            db.update_state(user_id, 'sell_Others_request')
            msg = 'You requested for approval to sell an item. What item do you want to sell?'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        else:
            db.update_state(user_id, 'home')
            msg = 'You cancelled the operation. Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.callback_query.from_user.first_name
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif state == 'buy':
        if data == 'None':
            msg = 'Sorry that we don\'t have the item you want. Would you like to be notified as soon as we have the item available?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
            db.update_state(user_id, 'buy_request')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            items = db.get_items_dict(category=data)
            msg = 'We have these items in that category:\n\n'
            keyboard = []
            for item in items:
                msg += '(%s) %s: %s [$%.2f]\n' % (item['item_id'], item['name'], item['description'], item['price'])
                keyboard.append([InlineKeyboardButton(item['item_id'], callback_data=item['item_id'])])
            msg += '\nWhich item would you like to buy?'
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='None')])
            keyboard = InlineKeyboardMarkup(keyboard)
            db.update_state(user_id, 'buy_item')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif state == 'buy_item':
        if data == 'None':
            msg = 'Sorry that we don\'t have the item you want. Would you like to be notified as soon as we have the item available?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
            db.update_state(user_id, 'buy_request')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        elif data == 'back':
            db.update_state(user_id, 'buy')
            msg = 'What are you buying? You can either type in the item ID or choose from the buttons below.'
            categories = []
            items = db.get_items_list()
            for category in [item[2] for item in items]:
                if category not in categories:
                    categories.append(category)
            keyboard = [[InlineKeyboardButton(category, callback_data=category)] for category in categories]
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='None')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            item = db.get_items_dict(item_id=data)
            msg = 'You want to buy %s: %s for $%.2f.\n\nIs this correct?' % (item['name'], item['description'], item['price'])
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
            db.update_state(user_id, 'buy_item_%s' % data)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif state.startswith('buy_item_'):
        if data == 'True':
            item = db.get_items_dict(item_id=state[9:])
            msg = 'Purchase successful! You have purchased %s: %s for $%.2f!\n\nWe will contact you as soon as possible to arrange for a delivery time that is convenient for you! Thank you for using Pipsqueak!' % (item['name'], item['description'], item['price'])
            db.update_state(user_id, 'home')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            global admin_id
            users_list = db.get_users(True)
            seller_name = users_list[[user[0] for user in users_list].index(item['seller_id'])][1]
            msg = 'Purchase: %s (%d) has purchased item %s: %s from %s (%d)\n\nWould you like to contact the seller now?' % (update.callback_query.from_user.name, user_id, item['item_id'], item['name'], seller_name, item['seller_id'])
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact now', callback_data='%d_%s' % (item['seller_id'], seller_name))]])
            bot.send_message(admin_id, msg, reply_markup=keyboard)
        else:
            db.update_state(user_id, 'home')
            msg = 'Purchase cancelled. Thank you for using Pipsqueak!'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif state == 'buy_request':
        if data == 'True':
            db.update_state(user_id, 'buy_request_item')
            msg = 'What item were you looking for?'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        else:
            db.update_state(user_id, 'home')
            msg = 'Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.callback_query.from_user.first_name
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    else:
        msg = 'Please use /start to begin trading!'
        bot.send_message(user_id, msg)


# Message Handlers
def message_handler(bot, update):
    global db
    global admin_id
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state == 'sell_Others_request':
        text = update.message.text
        msg = 'Request: %s (%d) has requested to sell the following item: %s.\n\nDo you approve of this listing?' % (update.message.from_user.name, user_id, text)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True_%d_%s' % (user_id, text)), InlineKeyboardButton('No', callback_data='False_%d_%s' % (user_id, text))]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
        msg = 'We have sent your request to an admin. We will get back to you as soon as possible. Thank you for using Pipsqueak!'
        db.update_state(user_id, 'home')
        bot.send_message(user_id, msg)
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
            msg = 'You item has been successfully listed!\nThank you for using Pipsqueak, %s! We will inform you as soon as someone offers to buy your item! We hope to see you soon!' % update.message.from_user.first_name
            bot.send_message(user_id, msg)
    elif state == 'buy_request_item':
        item = update.message.text
        name = update.message.from_user.name
        db.add_request(user_id, name, item)
        msg = '%s (%d) has requested for notification for the following item: %s' % (name, user_id, item)
        bot.send_message(admin_id, msg)
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak, %s! We will notify you as soon as the item is available!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    elif state == 'buy':
        item_id = update.message.text
        item = db.get_items_dict(item_id=item_id)
        msg = 'You want to buy %s: %s for $%.2f.\n\nIs this correct?' % (item['name'], item['description'], item['price'])
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data=False)]])
        db.update_state(user_id, 'buy_item_%s' % item_id)
        bot.send_message(user_id, msg, reply_markup=keyboard)
    elif state.startswith('forward_'):
        text = update.message.text
        state_list = state.split('_')
        target_id = int(state_list[1])
        bot.send_message(target_id, text)
    elif state == 'feedback':
        msg_id = update.message.message_id
        bot.forward_message(admin_id, user_id, msg_id)
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
    dispatcher.add_handler(CommandHandler('buy', buy_command))
    dispatcher.add_handler(CommandHandler('feedback', feedback))
    dispatcher.add_handler(CommandHandler('cancel', cancel))

    dispatcher.add_handler(MessageHandler(filters.Filters.all, message_handler))

    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    admin_id = 111914928
    main()