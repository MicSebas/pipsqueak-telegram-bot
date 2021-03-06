import telegram
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError
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
        msg = 'Hello, %s! Welcome to Pipsqueak, the marketplace by SUTD students for SUTD students!\n\nYou can /buy, /sell, and /browse spare parts and other items.\n\nYou can use /feedback to help us improve this platform for you!\n\nUse /name_mascot to enter the competition to name our new mascot!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)


def done(bot, update):
    global db
    global admins
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state.startswith('sell') or state.startswith('buy'):
        msg = 'You are in the middle of a transaction. Please use /cancel if you want to cancel the transaction.'
        bot.send_message(user_id, msg)
    elif state.startswith('forward_'):
        global admin_id
        if user_id not in admins:
            msg = 'The admin is still talking to you. It might be important.'
            bot.send_message(user_id, msg)
        else:
            buyer_id = int(state.split('_')[1])
            db.update_state(user_id, 'home')
            name = db.get_name(buyer_id)
            msg = 'You are no longer connected to %s.' % name
            bot.send_message(user_id, msg)
            msg = 'You are no longer connected to the admin. We hope to see you again soon!'
            db.update_state(buyer_id, 'home')
            bot.send_message(buyer_id, msg)
    elif state == 'feedback':
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
    elif state.startswith('forward_'):
        global admin_id
        if user_id != admin_id:
            msg = 'The admin is still talking to you. It might be important.'
            bot.send_message(user_id, msg)
        else:
            buyer_id = int(state.split('_')[1])
            db.update_state(admin_id, 'home')
            msg = 'You are no longer connected to the buyer.'
            bot.send_message(admin_id, msg)
            msg = 'You are no longer connected to the admin. We hope to see you again soon!'
            db.update_state(buyer_id, 'home')
            bot.send_message(buyer_id, msg)
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


def help_command(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        db.update_state(user_id, 'help')
        msg = 'I can connect you to an admin to help you better. Should I do that for you?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)


def force_cancel(bot, update):
    global db
    user_id = update.message.from_user.id
    db.update_state(user_id, 'home')
    msg = 'Back to home state'
    bot.send_message(user_id, msg)


def browse(bot, update):
    user_id = update.message.from_user.id
    pre_check(user_id, update.message.from_user.name)
    items = db.get_items_list()
    if items:
        filename = 'Pipsqueak_catalog.csv'
        f = open(filename, 'w')
        f.write('Date Listed, Item ID, Category, Item, Description, Quantity, Price\n')
        items = db.get_items_list()
        for item in items:
            date = item[0]
            item_id = item[1]
            category = item[2]
            name = item[3]
            if ',' in name:
                name = ' '.join(name.split(','))
            description = item[4]
            if ',' in description:
                description = ' '.join(description.split(','))
            quantity = item[5]
            price = item[6]
            f.write('%s, %s, %s, %s, %s, %d, $%.2f\n' % (date, item_id, category, name, description, quantity, price))
        f.close()
        msg = 'Here are the items currently listed at Pipsqueak!'
        bot.send_document(user_id, open(filename, 'rb'), caption=msg)
    else:
        msg = 'We currently don\'t have any items listed. Please come back and check again soon!'
        bot.send_message(user_id, msg)


def sell_command(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name, 'sell')
    if state != 'home' and state != 'sell':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        if state == 'home':
            db.update_state(user_id, 'sell')
        msg = 'What kind of item are you selling?'
        msg += '\n\nPlease note that due to company policy, we will not list any item that can be acquired from the Fab Lab for free. We seek your kind understanding on this matter.'
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
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        global db
        if state == 'home':
            db.update_state(user_id, 'buy')
        msg = 'What are you buying? You can either type in the item ID or choose from the buttons below.'
        categories = []
        items = db.get_items_list()
        if items:
            for category in [item[2] for item in items]:
                if category not in categories:
                    categories.append(category)
            keyboard = [[InlineKeyboardButton(category, callback_data=category)] for category in categories]
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='None')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.send_message(user_id, msg, reply_markup=keyboard)
        else:
            msg = 'We currently don\'t have any items listed. Please come back and check again soon!'
            db.update_state(user_id, 'home')
            bot.send_message(user_id, msg)


def feedback(bot, update):
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        global db
        msg = 'You are now connected to an admin. I will forward everything you say to them.\nUse /done when you\'re finished!'
        db.update_state(user_id, 'feedback')
        bot.send_message(user_id, msg)


def delete_listing(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        items = db.get_items_dict(seller_id=user_id)
        if items:
            msg = 'Which listing do you want to delete?\n\n'
            keyboard = []
            for item in items:
                msg += '(%s) %s: %s\n' % (item['item_id'], item['name'], item['description'])
                keyboard.append([InlineKeyboardButton(item['item_id'], callback_data=item['item_id'])])
            msg = msg.strip()
            keyboard = InlineKeyboardMarkup(keyboard)
            db.update_state(user_id, 'delete')
            bot.send_message(user_id, msg, reply_markup=keyboard)
        else:
            msg = 'You currently don\'t have any items listed.'
            bot.send_message(user_id, msg)


def admin_delete(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        items = db.get_items_list(in_transaction=True)
        if items:
            msg = 'Which listing do you want to delete?\n\n'
            keyboard = []
            for item in items:
                msg += '(%s) %s: %s\n' % (item[0], item[1], item[2])
                keyboard.append([InlineKeyboardButton(item[0], callback_data=item[0])])
            msg = msg.strip()
            keyboard = InlineKeyboardMarkup(keyboard)
            db.update_state(user_id, 'delete')
            bot.send_message(user_id, msg, reply_markup=keyboard)
        else:
            msg = 'There are currently no items in transaction.'
            bot.send_message(user_id, msg)


def admin_forward(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        msg = 'Who do you want to connect to?'
        db.update_state(user_id, 'forward')
        bot.send_message(user_id, msg)


def admin_broadcast(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        db.update_state(user_id, 'broadcast')
        msg = 'Send the message you want to broadcast.'
        bot.send_message(user_id, msg)


def name_mascot(bot, update):
    global db
    user_id = update.message.from_user.id
    state = pre_check(user_id, update.message.from_user.name)
    if state != 'home':
        msg = 'You\'re in the middle of an operation. Please finish what you are currently doing first or /cancel.'
        bot.send_message(user_id, msg)
    else:
        db.update_state(user_id, 'name')
        msg = 'What name do you want to give to our new mascot?'
        bot.send_message(user_id, msg)


# Callback Query Handlers
def callback_query_handler(bot, update):
    global db
    global admin_id
    user_id = update.callback_query.from_user.id
    state = db.get_state(user_id)
    data = update.callback_query.data
    msg_id = update.callback_query.message.message_id
    if update.callback_query.message.text.startswith('Approval: '):
        data = data.split('_')
        if data[0] == 'True':
            item_id = data[2]
            msg = 'Request approved: item %s.' % item_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            seller_id = int(data[1])
            db.update_item(item_id, 'status', 'Ready')
            item = db.get_items_dict(item_id=item_id)
            msg = 'Your listing of %s has been approved with item ID %s. We will contact you as soon as you have a buyer for your item! Thank you for using Pipsqueak!' % (item['name'], item_id)
            bot.send_message(seller_id, msg)
        elif data[0] == 'False':
            msg = 'Request denied.'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            seller_id = int(data[1])
            item_id = data[2]
            item = db.get_items_dict(item_id=item_id)
            db.delete_item(item_id)
            msg = 'Admin has unfortunately rejected your request to sell the following item: %s.\n\nWe have to filter the items that we provide to ensure they follow our company and community guidelines (e.g. not selling things you can get from the Fab Lab for free). We seek your kind understanding on this matter.' % item['name']
            bot.send_message(seller_id, msg)
        else:
            seller_id = int(data[1])
            item_id = data[2]
            name = db.get_name(seller_id)
            keyboard = InlineKeyboardButton([[InlineKeyboardButton('Yes', callback_data='True_%d_%s' % (seller_id, item_id)), InlineKeyboardButton('No', callback_data='False_%d_%s' % (seller_id, item_id))]])
            bot.edit_message_reply_markup(user_id, msg_id, reply_markup=keyboard)
            msg = 'Connecting to %s.' % name
            db.update_state(user_id, 'forward_%d' % seller_id)
            bot.send_message(user_id, msg)
            msg = 'An admin is trying to contact you regarding your item. Do you want to be connected to an admin now?\n\nNote that this will override your current operation.'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect me now', callback_data='forward_%d' % user_id)]])
            bot.send_message(seller_id, msg, reply_markup=keyboard)
    # elif update.callback_query.message.text.startswith('Request: '):
    #     data = data.split('_')
    #     if data[0] == 'True':
    #         msg = 'Request approved.'
    #         bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    #         seller_id = int(data[1])
    #         item = data[2]
    #         item_id = db.add_new_item('Others', seller_id)
    #         db.update_item(item_id, 'name', item)
    #         db.update_state(seller_id, 'sell_%s_description' % item_id)
    #         msg = 'Admin has APPROVED your request to sell the following item: %s.\n\nPlease send a short description to help potential buyers.' % item
    #         bot.send_message(seller_id, msg)
    #     elif data[0] == 'False':
    #         msg = 'Request denied.'
    #         bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    #         seller_id = int(data[1])
    #         item = data[2]
    #         msg = 'Admin has unfortunately rejected your request to sell the following item: %s.\n\nWe have to filter the items that we provide to ensure they follow our company and community guidelines (e.g. not selling things you can get from the Fab Lab for free). We seek your kind understanding on this matter.' % item
    #         bot.send_message(seller_id, msg)
    #     else:
    #         seller_id = int(data[1])
    #         item = data[2]
    #         name = db.get_name(seller_id)
    #         keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True_%d_%s' % (seller_id, item)), InlineKeyboardButton('No', callback_data='False_%d_%s' % (seller_id, item))]])
    #         bot.edit_message_reply_markup(user_id, msg_id, reply_markup=keyboard)
    #         msg = 'Connecting to %s.' % name
    #         db.update_state(user_id, 'forward_%d' % seller_id)
    #         bot.send_message(user_id, msg)
    #         msg = 'An admin is trying to contact you regarding your item. Do you want to be connected to an admin now?\n\nNote that this will override your current operation.'
    #         keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect me now', callback_data='forward_%d' % admin_id)]])
    #         bot.send_message(seller_id, msg, reply_markup=keyboard)
    elif update.callback_query.message.text.startswith('Purchase: '):
        [item_id, seller_id] = data.split('_')
        seller_id = int(seller_id)
        db.update_state(user_id, 'forward_%d' % seller_id)
        seller_name = db.get_name(seller_id)
        msg = update.callback_query.message.text
        msg += '\n\nConnecting to %s.' % seller_name
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        item = db.get_items_dict(item_id=item_id)
        msg = 'Congratulations, someone wants to purchase your %s (%s)! Do you want to be connected to an admin now to arrange for delivery time?\n\nNote that this will override your current operation.' % (item['name'], item_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect me now', callback_data=item_id)]])
        bot.send_message(seller_id, msg, reply_markup=keyboard)
    elif update.callback_query.message.text.startswith('Congratulations, '):
        db.update_state(user_id, 'forward_%d' % admin_id)
        msg = 'You are now connected to an admin.'
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        msg = '%s is connected!' % update.callback_query.from_user.name
        item = db.get_items_dict(item_id=data)
        buyer_id = item['status']
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect to buyer', callback_data='forward_%s' % buyer_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif update.callback_query.message.text.startswith('An admin is trying to'):
        db.update_state(user_id, 'forward_%d' % admin_id)
        msg = 'You are now connected to an admin.'
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        db.update_state(admin_id, 'forward_%d' % user_id)
        msg = '%s is connected! Use /done when you\'re finished.' % update.callback_query.from_user.name
        bot.send_message(admin_id, msg, reply_markup=None)
    elif update.callback_query.message.text.startswith('Help: '):
        db.update_state(user_id, 'forward_%s' % data)
        msg = '%s is now connected to %s.' % (db.get_name(user_id), db.get_name(int(data)))
        bot.edit_message_text(msg, admin_id, msg_id, reply_markup=None)
        msg = 'You are now connected to %s. Use /done when you\'re finished.' % db.get_name(int(data))
        bot.send_message(user_id, msg)
        db.update_state(int(data), 'forward_%d' % user_id)
        msg = 'You are now connected to an admin.'
        bot.send_message(int(data), msg)
    elif state == 'delete':
        db.delete_item(data)
        msg = 'Item %s successfully deleted!' % data
        db.update_state(user_id, 'home')
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif state == 'help':
        if data == 'True':
            db.update_state(user_id, 'home')
            msg = 'We are connecting you to an admin to assist you. Please hold.'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            msg = 'Help: %s is trying to contact you via the helpline.' % update.message.from_user.name
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect to %s' % update.message.from_user.name, callback_data=str(user_id))]])
            bot.send_message(admin_id, msg, reply_markup=keyboard)
        else:
            db.update_state(user_id, 'home')
            msg = 'Command cancelled.'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif state.startswith('forward_'):
        if data.startswith('forward_') and user_id == admin_id:
            seller_id = int(state.split('_')[1])
            db.update_state(seller_id, 'home')
            msg = 'Thank you for using Pipsqueak! We hope to see you again soon!'
            bot.send_message(seller_id, msg)
            buyer_id = int(data.split('_')[1])
            buyer_name = db.get_name(buyer_id)
            db.update_state(user_id, data)
            msg = 'Connecting to %s.' % buyer_name
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            msg = 'An admin is trying to contact you to arrange delivery time. Do you want to be connected to an admin now?\n\nNote that this will override your current operation.'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect me now', callback_data='forward_%d' % admin_id)]])
            bot.send_message(buyer_id, msg, reply_markup=keyboard)
    elif state == 'sell':
        # if data != 'Others':
        item_id = db.add_new_item(data, user_id)
        db.update_state(user_id, 'sell_%s_name' % item_id)
        if data != 'Others':
            msg = 'What %s are you selling?' % data.lower()
        else:
            msg = 'What item are you selling?'
        if data == 'Electronics':
            msg += '\n\nPlease note that due to company policy, we will not list any item that can be acquired from the Fab Lab for free. We seek your kind understanding on this matter.'
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    #     else:
    #         db.update_state(user_id, 'sell_Others')
    #         msg = 'You requested to sell an item which we may not be prepared to host.\n\nBefore proceeding, please note that your request may be moderated and subject to approval. Do you want to continue?'
    #         keyboard = [[InlineKeyboardButton('Yes', callback_data='Yes'), InlineKeyboardButton('No', callback_data='No')]]
    #         keyboard = InlineKeyboardMarkup(keyboard)
    #         bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    # elif state == 'sell_Others':
    #     if data == 'Yes':
    #         db.update_state(user_id, 'sell_Others_request')
    #         msg = 'You requested for approval to sell an item. What item do you want to sell?'
    #         bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    #     else:
    #         db.update_state(user_id, 'home')
    #         msg = 'You cancelled the operation. Thank you for using Pipsqueak! We hope to see you again soon, %s!' % update.callback_query.from_user.first_name
    #         bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif state.startswith('sell_') and state.endswith('_confirm'):
        if data == 'True':
            db.update_state(user_id, 'home')
            state_list = state.split('_')
            item_id = state_list[1]
            item = db.get_items_dict(item_id=item_id)
            msg = 'Your item listing of %s: %s for $%.2f has been sent for processing! Thank you for using Pipsqueak and we hope to see you again soon!' % (item['name'], item['description'], item['price'])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            msg = 'Approval: %s (%d) has requested to list %s: %s for $%.2f.\n\nDo you approve of this listing?' % (update.callback_query.from_user.name, user_id, item['name'], item['description'], item['price'])
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True_%d_%s' % (user_id, item_id)), InlineKeyboardButton('No', callback_data='False_%d_%s' % (user_id, item_id)), InlineKeyboardButton('Contact', callback_data='Contact_%d_%s' % (user_id, item_id))]])
            bot.send_message(admin_id, msg, reply_markup=keyboard)
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
                msg += '(%s) %s: %s [$%.2f each, %d available]\n\n' % (item['item_id'], item['name'], item['description'], item['price'], item['quantity'])
                keyboard.append([InlineKeyboardButton(item['item_id'], callback_data=item['item_id'])])
            msg += 'Which item would you like to buy?'
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
            if user_id == item['seller_id']:
                msg = 'You can\'t buy your own listing!'
                db.update_state(user_id, 'home')
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            else:
                msg = 'Buying %s: %s.\n\nHow many do you want to buy?' % (item['name'], item['description'])
                db.update_state(user_id, 'buy_item_%s' % data)
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif state.startswith('confirm_buy_item_'):
        if data == 'True':
            item = db.get_items_dict(item_id=state[9:])
            msg = 'Purchase successful! You have purchased %s: %s, %d for $%.2f!\n\nWe will contact you as soon as possible to arrange for a delivery time that is convenient for you! Thank you for using Pipsqueak!' % (item['name'], item['description'], item['quantity'], item['price']*item['quantity'])
            db.update_state(user_id, 'home')
            db.update_item(item['item_id'], 'status', str(user_id))
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
            seller_id = item['seller_id']
            seller_name = db.get_name(seller_id)
            msg = 'Purchase: %s (%d) has purchased item %s: %s from %s (%d)\n\nWould you like to contact the seller now?' % (update.callback_query.from_user.name, user_id, item['item_id'], item['name'], seller_name, item['seller_id'])
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact seller now', callback_data='%s_%d' % (item['item_id'], seller_id))]])
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
    if state.startswith('sell_'):  # and not state.startswith('sell_Others'):
        [_, item_id, column] = state.split('_')
        text = update.message.text
        success = db.update_item(item_id, column, text)
        if not success:
            msg = 'That is not a valid amount. Pleas try again.'
            bot.send_message(user_id, msg)
        else:
            if column == 'name':
                db.update_state(user_id, 'sell_%s_description' % item_id)
                msg = 'Please send a short description of your item to help potential buyers.'
                bot.send_message(user_id, msg)
            elif column == 'description':
                db.update_state(user_id, 'sell_%s_quantity' % item_id)
                msg = 'How many of this item are you selling?'
                bot.send_message(user_id, msg)
            elif column == 'quantity':
                db.update_state(user_id, 'sell_%s_price' % item_id)
                msg = 'How much are you selling each item for?'
                bot.send_message(user_id, msg)
            else:
                db.update_state(user_id, 'sell_%s_confirm' % item_id)
                item = db.get_items_dict(item_id=item_id)
                msg = 'You want to sell %s: %s, %d for $%.2f each.\n\nIs this correct?' % (item['name'], item['description'], item['quantity'], item['price'])
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
                bot.send_message(user_id, msg, reply_markup=keyboard)
    elif state == 'buy_request_item':
        item = update.message.text
        name = update.message.from_user.name
        db.add_request(user_id, name, item)
        msg = '%s (%d) has requested for notification for the following item: %s' % (name, user_id, item)
        bot.send_message(admin_id, msg)
        db.update_state(user_id, 'home')
        msg = 'Thank you for using Pipsqueak, %s! We will notify you as soon as the item is available!' % update.message.from_user.first_name
        bot.send_message(user_id, msg)
    elif state == 'buy' or state == 'buy_item':
        item_id = update.message.text
        item = db.get_items_dict(item_id=item_id)
        if item:
            msg = 'You want to buy %s: %s for $%.2f.\n\nIs this correct?' % (item['name'], item['description'], item['price'])
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
            db.update_state(user_id, 'buy_item_%s' % item_id)
            bot.send_message(user_id, msg, reply_markup=keyboard)
        else:
            msg = 'There is no item with that code. Please try again.'
            bot.send_message(user_id, msg)
    elif state.startswith('buy_item_'):
        quantity = int(update.message.text)
        item_id = state.split('_')[-1]
        db.update_item(item_id, 'quantity', quantity)
        item = db.get_items_dict(item_id=item_id)
        msg = 'You want to buy %s: %s\nPurchase quantity: %d\nTotal price: $%.2f\n\nIs this correct?' % (item['name'], item['description'], quantity, item['price'])
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='True'), InlineKeyboardButton('No', callback_data='False')]])
        db.update_state(user_id, 'confirm_buy_item_%s' % item_id)
        bot.send_message(user_id, msg, reply_markup=keyboard)
    elif state == 'forward':
        users = db.get_users(True)
        text = update.message.text
        found = False
        for user in users:
            if text.lower() == user[1].lower() or '@' + text.lower() == user[1].lower():
                db.update_state(user_id, 'forward_%d' % user[0])
                msg = 'Connecting to %s.' % user[1]
                bot.send_message(user_id, msg)
                msg = 'An admin is trying to contact you. Do you want to be connected to an admin now?\n\nNote that this will override your current operation.'
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect me now', callback_data='forward_%d' % user_id)]])
                bot.send_message(user[0], msg, reply_markup=keyboard)
                found = True
                break
        if not found:
            msg = 'There is no user with that name. Please try again.'
            bot.send_message(user_id, msg)
    elif state.startswith('forward_'):
        text = update.message.text
        state_list = state.split('_')
        target_id = int(state_list[1])
        bot.send_message(target_id, text)
    elif state == 'feedback':
        msg_id = update.message.message_id
        db.add_feedback(user_id, update.message.from_user.name, update.message.text)
        bot.forward_message(admin_id, user_id, msg_id)
    elif state == 'broadcast':
        text = 'BROADCAST MESSAGE FROM ADMIN:\n\n' + update.message.text
        db.update_state(user_id, 'home')
        bot.send_message(user_id, 'Broadcasting message...')
        all_users = db.get_users()
        for user in all_users:
            try:
                bot.send_message(user, text)
                print('Sent to %d' % user)
            except TelegramError:
                print('Failed sending to %d' % user)
        msg = 'Message broadcast successful!'
        bot.send_message(user_id, msg)
    elif state == 'name':
        text = update.message.text
        name = update.message.from_user.name
        db.add_mascot_name(user_id, name, text)
        db.update_state(user_id, 'home')
        msg = 'Your submission has been received! Thank you for using Pipsqueak!'
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
    dispatcher.add_handler(CommandHandler('_cancel', force_cancel))
    dispatcher.add_handler(CommandHandler('buy', buy_command))
    dispatcher.add_handler(CommandHandler('feedback', feedback))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CommandHandler('delete_listing', delete_listing))
    dispatcher.add_handler(CommandHandler('_delete', admin_delete))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('_forward', admin_forward))
    dispatcher.add_handler(CommandHandler('_broadcast', admin_broadcast))
    dispatcher.add_handler(CommandHandler('name_mascot', name_mascot))

    dispatcher.add_handler(MessageHandler(filters.Filters.all, message_handler))

    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    admin_id = -258851839
    admins = (111914928, 230937024, 255484909, 42010966)
    main()
