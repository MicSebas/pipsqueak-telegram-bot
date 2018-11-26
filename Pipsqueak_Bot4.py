import telegram
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, TelegramError
from Database2 import Database
import json

TOKEN = '666724238:AAF2SyvjZbui0VMbPOlG3op2jgMQFVFM_yg'
PORT = int(os.environ.get('PORT', '5000'))
BOT = telegram.Bot(token=TOKEN)
BOT.setWebhook(url='https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)


def precheck(update):
    global db
    if update.callback_query is not None:
        user_id = update.callback_query.from_user.id
        name = update.callback_query.from_user.name
    else:
        user_id = update.message.from_user.id
        name = update.message.from_user.name
    users_list = db.get_users()
    if user_id in users_list:
        state = db.get_state(user_id)
    else:
        db.add_new_user(user_id, name)
        state = {'state': 'home', 'substate': 'home', 'item_state': None}
    if state['state'] != 'forward' and state['state'] != 'broadcast':
        if update.callback_query is not None:
            activity = 'Button: ' + update.callback_query.data
        else:
            activity = 'Message: ' + update.message.text
        db.add_activity(user_id, name, state, activity)
    return user_id, state


def start(bot, update):
    global db
    user_id, state = precheck(update)
    if state['state'] == 'home':
        db.update_state(user_id, 'home')
        msg = 'Hello, %s! Welcome to Pipsqueak, the first online parts marketplace in SUTD! How can I help you today?' % update.message.from_user.first_name
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('I want to /buy things', callback_data='buy')],
                                         [InlineKeyboardButton('I want to /sell things', callback_data='sell')],
                                         [InlineKeyboardButton('Contact an admin', callback_data='help')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
        bot.send_message(user_id, msg)


def cancel(bot, update):
    global db
    user_id, state = precheck(update)
    if state['state'] == 'home':
        msg = 'Please use /start to begin trading!'
        if update.callback_query is not None:
            query_id = update.callback_query.id
            bot.answer_callback_query(query_id, msg)
        else:
            bot.send_message(user_id, msg)
    elif state['state'] == 'forward' or state['state'] == 'feedback':
        done(bot, update)
    else:
        state = {'state': 'home', 'substate': 'home', 'item_state': None}
        db.update_state(user_id, state)
        msg = 'Operation cancelled. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        if update.callback_query is not None:
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            bot.send_message(user_id, msg, reply_markup=keyboard)


def done(bot, update):
    global db
    global admins
    global admin_id
    user_id, state = precheck(update)
    if state['state'] == 'home':
        msg = 'Please use /start to begin trading!'
        if update.callback_query is not None:
            query_id = update.callback_query.id
            bot.answer_callback_query(query_id, msg)
        else:
            bot.send_message(user_id, msg)
    elif state['state'] == 'forward':
        target_id = int(state['substate'])
        state = {'state': 'home', 'substate': 'home', 'item_state': None}
        msg = 'You are no longer connected. Thank you for using Pipsqueak!'
        for num in [user_id, target_id]:
            db.update_state(num, state)
            if num not in admins:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
            else:
                keyboard = None
            bot.send_message(num, msg, reply_markup=keyboard)
    elif state['state'] == 'feedback':
        state = {'state': 'home', 'substate': 'home', 'item_state': None}
        db.update_state(user_id, state)
        msg = 'Your feedback has been received! We will try our best to be better for you! Thank you for using Pipsqueak!'
        bot.send_message(user_id, msg)
        msg = 'End of feedback from %s' % update.message.from_user.name
        bot.send_message(admin_id, msg)
    else:
        cancel(bot, update)


def help_command(bot, update):
    global db
    user_id, state = precheck(update)
    state['state'] = 'help'
    state['substate'] = 'confirm'
    db.update_state(user_id, state)
    msg = 'We can connect you to an admin to help assist you better. Do you want to proceed?'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='yes'), InlineKeyboardButton('No', callback_data='no')]])
    if update.callback_query is not None:
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        bot.send_message(user_id, msg, reply_markup=keyboard)


def help_confirm(bot, update):
    global db
    global admin_id
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    state = {'state': 'home', 'substate': 'home', 'item_state': None}
    db.update_state(user_id, state)
    if data == 'yes':
        msg = 'We are connecting you to an admin. Please hold.'
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        name = update.callback_query.from_user.name
        msg = 'Help: %s (%d) is trying to connect to an admin.' % (update.callback_query.from_user.name, user_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect to %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    else:
        cancel(bot, update)


def feedback(bot, update):
    global db
    global admin_id
    user_id, state = precheck(update)
    if state['state'] == 'home':
        if update.callback_query is not None:
            msg_id = update.callback_query.message.message_id
            bot.edit_message_reply_markup(user_id, msg_id, reply_markup=None)
        new_state = {'state': 'feedback', 'substate': None, 'item_state': None}
        db.update_state(user_id, new_state)
        msg = 'Your feedback is very valuable to us! Please tell us how we can improve to serve you better, be as specific as you like! Note that we currently can only receive feedback in text.\n\nUse /done when you\'re finished.'
        bot.send_message(user_id, msg)
        msg = 'Feedback from %s:' % db.get_name(user_id)
        bot.send_message(admin_id, msg)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
        bot.send_message(user_id, msg)


# Admin functions
def force_cancel(bot, update):
    global db
    user_id, state = precheck(update)
    new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
    db.update_state(user_id, new_state)
    msg = 'Back to home state'
    bot.send_message(user_id, msg)


def force_state(bot, update):
    user_id, state = precheck(update)
    msg = json.dumps(state)
    bot.send_message(user_id, msg)


def broadcast_command(bot, update):
    global db
    global admins
    user_id, state = precheck(update)
    if user_id in admins:
        if state['state'] != 'home':
            msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
            bot.send_message(user_id, msg)
        else:
            state['state'] = 'broadcast'
            state['substate'] = None
            state['item_state'] = None
            db.update_state(user_id, state)
            msg = 'Send me the message you want to broadcast.'
            bot.send_message(user_id, msg)
    else:
        msg = 'You\'re not authorized to use this function.'
        bot.send_message(user_id, msg)


def broadcast_message(bot, update):
    global db
    user_id = update.message.from_user.id
    text = update.message.text
    msg = 'BROADCAST MESSAGE FROM ADMIN:\n\n' + text
    all_users = db.get_users()
    for user in all_users:
        try:
            bot.send_message(user, msg)
        except TelegramError:
            pass
    state = {'state': 'home', 'substate': 'home', 'item_state': None}
    db.update_state(user_id, state)
    msg = 'Finished broadcasting message!'
    bot.send_message(user_id, msg)


def admin_forward(bot, update):
    global db
    global admins
    user_id, state = precheck(update)
    if user_id in admins:
        if state['state'] != 'home':
            msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
            bot.send_message(user_id, msg)
        else:
            state['state'] = 'forward'
            state['substate'] = None
            state['item_state'] = None
            db.update_state(user_id, state)
            msg = 'Who do you want to connect to?'
            bot.send_message(user_id, msg)
    else:
        msg = 'You\'re not authorized to use this function.'
        bot.send_message(user_id, msg)


def forward_connect(bot, update, state):
    global db
    if update.callback_query is not None:
        user_id = update.callback_query.from_user.id
        data = update.callback_query.data
        target_id = int(data.split('_')[1])
    else:
        user_id = update.message.from_user.id
        users = db.get_users(True)
        text = update.message.text
        target_id = 0
        for user in users:
            if text.lower() == user[1].lower() or '@' + text.lower() == user[1].lower():
                target_id = user[0]
                break
    if target_id != 0:
        state['substate'] = target_id
        name = db.get_name(target_id)
        db.update_state(user_id, state)
        msg = 'Waiting to connect to %s.' % name
        bot.send_message(user_id, msg)
        msg = 'An admin is connecting to you. Do note that connecting to an admin will override your current operations.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect now', callback_data='forward_%d' % user_id)]])
        bot.send_message(target_id, msg, reply_markup=keyboard)
    else:
        msg = 'There is no user with that name. Please try again.'
        bot.send_message(user_id, msg)


def review_request(bot, update, data):
    global db
    global admin_id
    name = update.callback_query.from_user.name
    msg_id = update.callback_query.message.message_id
    data = data.split('_')
    seller_id = int(data[1])
    item_name = '_'.join(data[2:])
    if data[0] == 'approve':
        # TODO: Finish this
        pass
    else:
        msg = 'Request from %s for %s rejected by %s' % (db.get_name(seller_id), item_name, name)
        bot.edit_message_text(msg, admin_id, msg_id)
        msg = 'Unfortunately, your request to list %s has been rejected by an admin.' % item_name
        bot.send_message(seller_id, msg)


# Buy/Sell/Marketplace functions
def buy(bot, update):
    global db
    user_id, state = precheck(update)
    if state['state'] == 'home':
        new_state = {'state': 'buy', 'substate': 'category', 'item_state': None}
        db.update_state(user_id, new_state)
        msg = 'What category of items do you want to buy?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='stationery')],
                                         [InlineKeyboardButton('IC chips', callback_data='ICs')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='none')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        if update.callback_query is not None:
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            bot.send_message(user_id, msg, reply_markup=keyboard)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
        bot.send_message(user_id, msg)


def sell(bot, update):
    global db
    user_id, state = precheck(update)
    if state['state'] == 'home':
        new_state = {'state': 'sell', 'substate': 'category', 'item_state': None}
        db.update_state(user_id, new_state)
        msg = 'What category of items do you want to sell?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='stationery')],
                                         [InlineKeyboardButton('IC chips', callback_data='ICs')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='request')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        if update.callback_query is not None:
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            bot.send_message(user_id, msg, reply_markup=keyboard)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
        bot.send_message(user_id, msg)


def category(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'request':
        request(bot, update)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        state['substate'] = 'item'
        state['item_state'] = {'category': data, 'page': 0}
        db.update_state(user_id, state)
        items = db.get_items(data, 0)
        msg = 'What %s do you want to %s?' % (data, 'buy' if state['state'] == 'marketplace' else state['state'])
        keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
        keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                         InlineKeyboardButton('Next >>', callback_data='next')])
        keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
        keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def choose_item(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'prev':
        if state['item_state']['page'] == 0:
            query_id = update.callback_query.id
            msg = 'There is no previous page!'
            bot.answer_callback_query(query_id, msg)
        else:
            state['item_state']['page'] -= 1
            db.update_state(user_id, state)
            items = db.get_items(state['item_state']['category'], state['item_state']['page'])
            msg = 'What %s do you want to %s?' % (state['item_state']['category'], state['state'])
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                             InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'next':
        items = db.get_items(state['item_state']['category'], state['item_state']['page'] + 1)
        if items:
            state['item_state']['page'] += 1
            db.update_state(user_id, state)
            msg = 'What %s do you want to %s?' % (state['item_state']['category'], state['state'])
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                             InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            query_id = update.callback_query.id
            msg = 'There is no next page!'
            bot.answer_callback_query(query_id, msg)
    elif data == 'category':
        state['substate'] = 'category'
        state['item_state'] = None
        db.update_state(user_id, state)
        msg = 'What category of items do you want to %s?' % 'buy' if state['state'] == 'marketplace' else state['state']
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='stationery')],
                                         [InlineKeyboardButton('IC chips', callback_data='ICs')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='request')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'request':
        request(bot, update)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        item_id = int(data)
        if state['state'] != 'marketplace':
            item = db.get_item_details(item_id)
            if item:
                options = item['options']
                if options is None or options == 'null':
                    state['item_state']['item_id'] = item_id
                    state['item_state']['item_name'] = item['itemName']
                    state['item_state']['properties'] = None
                    state['substate'] = 'quantity'
                    db.update_state(user_id, state)
                    if int(item['items']['quantity']) <= 0:
                        stock(bot, update, state)
                    else:
                        msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                        msg += 'Description: %s\n\n' % item['description']
                        if state['state'] != 'sell':
                            msg += 'We are selling at $%.2f each. ' % float(item['items']['price'])
                        msg += 'How many do you want to %s?' % state['state']
                        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                                         [InlineKeyboardButton('<< back', callback_data='back'),
                                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
                        msg_id = update.callback_query.message.message_id
                        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
                else:
                    options_list = [list(option.keys())[0] for option in options]
                    state['item_state']['item_id'] = item_id
                    state['item_state']['item_name'] = item['itemName']
                    state['item_state']['options'] = options_list
                    state['item_state']['index'] = 0
                    state['substate'] = 'options'
                    db.update_state(user_id, state)
                    msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                    msg += 'Description: %s\n\n' % item['description']
                    msg += 'What %s do you want to %s?' % (options_list[0].lower(), state['state'])
                    keyboard = [[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])]]
                    for option in options[0][options_list[0]]:
                        keyboard.append([InlineKeyboardButton(option, callback_data=option)])
                    keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
                    keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                                     InlineKeyboardButton('/cancel', callback_data='cancel')])
                    keyboard = InlineKeyboardMarkup(keyboard)
                    msg_id = update.callback_query.message.message_id
                    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                query_id = update.callback_query.id
                msg = 'That item doesn\'t exist.'
                bot.answer_callback_query(query_id, msg)
        else:
            item = db.get_item_details(item_id)
            state['item_state']['item_id'] = item_id
            state['item_state']['item_name'] = item['itemName']
            state['substate'] = 'seller'
            db.update_state(user_id, state)
            listings = db.get_listings(item_id)
            if listings:
                msg = 'We have these listings for %s:\n\n' % state['item_state']['item_name']
                keyboard = []
                for listing in listings:
                    if int(listing['quantity']) > 0:
                        msg += 'ID: %d\n' % int(listing['listingId'])
                        msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
                        msg += 'Quantity available: %d\n' % int(listing['quantity'])
                        msg += 'Price: $%.2f\n\n' % float(listing['price'])
                        keyboard.append([InlineKeyboardButton('ID %d' % int(listing['listingId']), callback_data=str(listing['listingId']))])
                msg += 'Which one do you want to buy?'
                keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
                keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                                 InlineKeyboardButton('/cancel', callback_data='cancel')])
                keyboard = InlineKeyboardMarkup(keyboard)
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                stock(bot, update, state)


def seller(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'request':
        request(bot, update)
    elif data == 'back':
        state['substate'] = 'item'
        del state['item_state']['item_id']
        del state['item_state']['item_name']
        item_category = state['item_state']['category']
        page = state['item_state']['page']
        db.update_state(user_id, state)
        items = db.get_items(item_category, page)
        msg = 'What %s do you want to buy?' % item_category
        keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
        keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                         InlineKeyboardButton('Next >>', callback_data='next')])
        keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
        keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        listing_id = int(data)
        state['substate'] = 'quantity'
        state['item_state']['listing_id'] = listing_id
        db.update_state(user_id, state)
        listing = db.get_listing_details(listing_id)
        if listing:
            msg = 'You want to buy %s\n' % listing['itemName']
            msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
            msg += 'Quantity available: %d\n' % int(listing['quantity'])
            msg += 'Price: $%.2f\n\n' % float(listing['price'])
            msg += 'How many do you want to buy?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                              InlineKeyboardButton('/cancel', callback_data='cancel')]])
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            stock(bot, update, state)


def choose_options(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.id
    if data.startswith('img '):
        img_url = 'http://phpstack-212261-643485.cloudwaysapps.com/image?upload=' + data[4:]
        bot.send_message(user_id, img_url)
    elif data == 'request':
        request(bot, update)
    elif data == 'back':
        if state['item_state']['index'] == 0:
            state['substate'] = 'item'
            del state['item_state']['item_id']
            del state['item_state']['item_name']
            del state['item_state']['options']
            del state['item_state']['index']
            item_category = state['item_state']['category']
            page = state['item_state']['page']
            db.update_state(user_id, state)
            items = db.get_items(item_category, page)
            msg = 'What %s do you want to %s?' % (item_category, state['state'])
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                             InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            item = db.get_item_details(state['item_state']['item_id'])
            options = item['options']
            options_list = [list(option.keys())[0] for option in options]
            state['item_state']['options'] = options_list
            state['item_state']['index'] = 0
            state['substate'] = 'options'
            db.update_state(user_id, state)
            msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
            msg += 'Description: %s\n\n' % item['description']
            msg += 'What %s do you want to %s?' % (options_list[0].lower(), state['state'])
            keyboard = [[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])]]
            for option in options[0][options_list[0]]:
                keyboard.append([InlineKeyboardButton(option, callback_data=option)])
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                             InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        item = db.get_item_details(state['item_state']['item_id'])
        index = state['item_state']['index']
        state['item_state']['options'][index] = data
        if index + 1 < len(state['item_state']['options']):
            index += 1
            state['item_state']['index'] = index
            msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
            msg += 'Description: %s\n\n' % item['description']
            msg += 'What %s do you want to %s?' % (state['item_state']['options'][index].lower(), state['state'])
            keyboard = [[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])]]
            for option in item['options'][index][state['item_state']['options'][index]]:
                keyboard.append([InlineKeyboardButton(option, callback_data=option)])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                             InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            state['item_state']['options'].reverse()
            properties = json.dumps(state['item_state']['options'], separators=(',', ':'))
            state['item_state']['properties'] = properties
            del state['item_state']['options']
            del state['item_state']['index']
            state['substate'] = 'quantity'
            db.update_state(user_id, state)
            if int(item['items'][properties]['quantity']) <= 0 and state['state'] == 'buy':
                stock(bot, update, state)
            else:
                msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                msg += 'Description: %s\n' % item['description']
                msg += 'Properties: %s\n\n' % ', '.join(json.loads(properties))
                if state['state'] != 'sell':
                    msg += 'We are selling at $%.2f each. ' % float(item['items'][properties]['price'])
                msg += 'How many do you want to %s?' % state['state']
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                                 [InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def quantity_callback_query(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'back':
        if state['state'] != 'marketplace':
            item = db.get_item_details(state['item_state']['item_id'])
            if state['item_state']['properties']:
                options = item['options']
                options_list = [list(option.keys())[0] for option in options]
                state['item_state']['options'] = options_list
                state['item_state']['index'] = 0
                state['substate'] = 'options'
                del state['item_state']['properties']
                db.update_state(user_id, state)
                msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                msg += 'Description: %s\n\n' % item['description']
                msg += 'What %s do you want to %s?' % (options_list[0].lower(), state['state'])
                keyboard = [[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])]]
                for option in options[0][options_list[0]]:
                    keyboard.append([InlineKeyboardButton(option, callback_data=option)])
                keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                                 InlineKeyboardButton('/cancel', callback_data='cancel')])
                keyboard = InlineKeyboardMarkup(keyboard)
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                state['substate'] = 'item'
                del state['item_state']['item_id']
                del state['item_state']['item_name']
                del state['item_state']['properties']
                item_category = state['item_state']['category']
                page = state['item_state']['page']
                db.update_state(user_id, state)
                items = db.get_items(item_category, page)
                msg = 'What %s do you want to %s?' % (item_category, state['state'])
                keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
                keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                                 InlineKeyboardButton('Next >>', callback_data='next')])
                keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
                keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
                keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
                keyboard = InlineKeyboardMarkup(keyboard)
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            del state['item_state']['listing_id']
            state['substate'] = 'seller'
            db.update_state(user_id, state)
            item_id = state['item_state']['item_id']
            listings = db.get_listings(item_id)
            if listings:
                msg = 'We have these listings for %s:\n\n' % state['item_state']['item_name']
                keyboard = []
                for listing in listings:
                    if int(listing['quantity']) > 0:
                        msg += 'ID: %d\n' % int(listing['listingId'])
                        msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
                        msg += 'Quantity available: %d\n' % int(listing['quantity'])
                        msg += 'Price: $%.2f\n\n' % float(listing['price'])
                        keyboard.append([InlineKeyboardButton('ID %d' % int(listing['listingId']), callback_data=str(listing['listingId']))])
                msg += 'Which one do you want to buy?'
                keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
                keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                                 InlineKeyboardButton('/cancel', callback_data='cancel')])
                keyboard = InlineKeyboardMarkup(keyboard)
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                stock(bot, update, state)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        img_url = 'http://phpstack-212261-643485.cloudwaysapps.com/image?upload=' + data[4:]
        bot.send_message(user_id, img_url)


def quantity_message(bot, update, state):
    global db
    user_id = update.message.from_user.id
    text = update.message.text
    try:
        quantity = int(text)
        if quantity <= 0:
            msg = 'That\'s not a valid quantity. Please try again.'
            bot.send_message(user_id, msg)
        else:
            if state['state'] == 'buy':
                item = db.get_item_details(state['item_state']['item_id'])
                in_stock = int(item['items'][state['item_state']['properties']])
                if quantity > in_stock:
                    msg = 'That\'s more than the stock we have. Please try again.'
                    bot.send_message(user_id, msg)
                else:
                    state['substate'] = 'confirm'
                    state['item_state']['quantity'] = quantity
                    db.update_state(user_id, state)
                    msg = 'You want to buy %s\n' % state['item_state']['item_name']
                    msg += 'Description: %s\n' % item['description']
                    if state['item_state']['properties']:
                        msg += 'Properties: %s\n' % ', '.join(json.loads(state['item_state']['properties']))
                    msg += 'Quantity: %d\n' % quantity
                    price = float(item['items'][state['item_state']['properties']]['price'])
                    if quantity > 1:
                        msg += 'Price: $%.2f each, $%.2f total\n\n' % (price, price * quantity)
                    else:
                        msg += 'Price: $%.2f\n\n' % price
                    msg += 'Alternatively, you can check the marketplace for student-listed items. '
                    msg += 'Please note that we will not be issuing receipts for marketplace purchases.\n\n'
                    msg += 'Would you like to buy now?'
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Buy now', callback_data='confirm')],
                                                     [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                                     [InlineKeyboardButton('<< back', callback_data='back'),
                                                      InlineKeyboardButton('/cancel', callback_data='cancel')]])
                    bot.send_message(user_id, msg, reply_markup=keyboard)
            elif state['state'] == 'sell':
                item = db.get_item_details(state['item_state']['item_id'])
                if state['item_state']['properties']:
                    price = float(item['items'][state['item_state']['properties']]['price'])
                else:
                    price = float(item['items']['price'])
                state['item_state']['quantity'] = quantity
                state['substate'] = 'price'
                db.update_state(user_id, state)
                msg = 'You want to sell %s\n' % state['item_state']['item_name']
                if state['item_state']['properties']:
                    msg += 'Properties: %s\n' % ', '.join(json.loads(state['item_state']['properties']))
                msg += 'Quantity: %d\n\n' % quantity
                msg += 'We are currently selling this item at $%.2f each. How much do you want to sell for?' % price
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.send_message(user_id, msg, reply_markup=keyboard)
            else:
                listing = db.get_listing_details(state['item_state']['listing_id'])
                in_stock = int(listing['quantity'])
                if quantity > in_stock:
                    msg = 'That\'s more than the stock they have. Please try again.'
                    bot.send_message(user_id, msg)
                else:
                    state['substate'] = 'confirm'
                    state['item_state']['quantity'] = quantity
                    db.update_state(user_id, state)
                    msg = 'You want to buy %s\n' % state['item_state']['item_name']
                    if listing['properties']:
                        msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
                    msg += 'Quantity: %d\n' % quantity
                    price = float(listing['price'])
                    if quantity > 1:
                        msg += 'Price: $%.2f each, $%.2f total\n\n' % (price, price * quantity)
                    else:
                        msg += 'Price: $%.2f\n\n' % price
                    msg += 'Alternatively, you can check the Pipsqueak store, '
                    msg += 'where we will be issuing receipts for your purchases.\n\n'
                    msg += 'Would you like to buy now?'
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Buy now', callback_data='confirm')],
                                                     [InlineKeyboardButton('Check store', callback_data='store')],
                                                     [InlineKeyboardButton('<< back', callback_data='back'),
                                                      InlineKeyboardButton('/cancel', callback_data='cancel')]])
                    bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid quantity. Please try again.'
        bot.send_message(user_id, msg)


def price_callback_query(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'back':
        item = db.get_item_details(state['item_state']['item_id'])
        del state['item_state']['quantity']
        state['substate'] = 'quantity'
        db.update_state(user_id, state)
        properties = state['item_state']['properties']
        msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
        msg += 'Description: %s\n' % item['description']
        msg += 'Properties: %s\n\n' % ', '.join(json.loads(properties))
        if state['state'] != 'sell':
            msg += 'We are selling at $%.2f each. ' % float(item['items'][properties]['price'])
        msg += 'How many do you want to sell?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                         [InlineKeyboardButton('<< back', callback_data='back'),
                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def price_message(bot, update, state):
    global db
    user_id = update.message.from_user.id
    text = update.message.text
    try:
        price = float(text)
        if price <= 0:
            msg = 'That\'s not a valid amount. Please try again.'
            bot.send_message(user_id, msg)
        else:
            state['substate'] = 'confirm'
            state['item_state']['price'] = price
            db.update_state(user_id, state)
            msg = 'You want to sell %s\n' % state['item_state']['item_name']
            if state['item_state']['properties']:
                msg += 'Properties: %s\n' % ', '.join(json.loads(state['item_state']['properties']))
            msg += 'Quantity: %d\n' % state['item_state']['quantity']
            msg += 'Price: $%.2f\n\n' % price
            msg += 'Is this correct?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Confirm', callback_data='confirm')],
                                             [InlineKeyboardButton('<< back', callback_data='back'),
                                              InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid amount. Please try again.'
        bot.send_message(user_id, msg)


def confirm(bot, update, state):
    global db
    global admin_id
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'confirm':
        if state['state'] == 'buy':
            item_state = state['item_state']
            item = db.get_item_details(item_state['item_id'])
            item_name = item_state['item_name']
            properties = item_state['properties']
            quantity = item_state['quantity']
            if properties:
                price = float(item['items'][properties]['price'])
            else:
                price = float(item['items']['price'])
            new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
            db.update_state(user_id, new_state)
            msg = 'Purchase successful!\n\n'
            msg += 'Item: %s\n' % item_name
            if properties:
                msg += 'Properties: %s\n' % ', '.join(json.loads(properties))
            msg += 'Quantity: %d\n' % quantity
            msg += 'Total price: $%.2f\n\n' % price * quantity
            msg += 'We will contact you soon for pickup details. Thank you for using Pipsqueak!'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            args = {'item': item_state['item_id'], 'quantity': quantity, 'telegramId': user_id}
            if properties:
                args['properties'] = properties
            text = db.bought_item(args)
            if True:
                # TODO: Check if user is already registered
                text_list = text.split('\n')
                msg = text_list[1]
                url = 'phpstack-212261-643485.cloudwaysapps.com/logon/register?telegramId=' + str(user_id)
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Complete registration', url=url)]])
                bot.send_message(user_id, msg, reply_markup=keyboard)
            msg = 'Purchase: %s (%d) has purchased the following item:\n\n' % (update.callback_query.from_user.name, user_id)
            msg += '%s (itemId: %d)\n' % (item_name, item_state['item_id'])
            if properties:
                msg += 'Properties: %s\n' % ', '.join(json.loads(properties))
            msg += 'Quantity: %d\n' % quantity
            msg += 'Total price: $%.2f\n\n' % price * quantity
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % update.callback_query.from_user.name, callback_data='forward_%d' % user_id)]])
            bot.send_message(admin_id, msg, reply_markup=keyboard)
        elif state['state'] == 'sell':
            item_state = state['item_state']
            item = db.get_item_details(item_state['item_id'])
            item_name = item_state['item_name']
            properties = item_state['properties']
            quantity = item_state['quantity']
            if properties:
                price = float(item['items'][properties]['price'])
            else:
                price = float(item['items']['price'])
            new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
            db.update_state(user_id, new_state)
            msg = 'Listing successful!\n\n'
            msg += 'Item: %s\n' % item_name
            if properties:
                msg += 'Properties: %s\n' % ', '.join(json.loads(properties))
            msg += 'Quantity: %d\n' % quantity
            msg += 'Price: $%.2f\n\n' % price
            msg += 'We will contact you as soon as you have a buyer. Thank you for using Pipsqueak!'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            # TODO: Update listing database
            msg = 'Listing: %s (%d) has purchased the following item:\n\n' % (update.callback_query.from_user.name, user_id)
            msg += '%s (itemId: %d)\n' % (item_name, item_state['item_id'])
            if properties:
                msg += 'Properties: %s\n' % ', '.join(json.loads(properties))
            msg += 'Quantity: %d\n' % quantity
            msg += 'Price: $%.2f' % price
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % update.callback_query.from_user.name, callback_data='forward_%d' % user_id)]])
            bot.send_message(admin_id, msg, reply_markup=keyboard)
        else:
            item_state = state['item_state']
            listing = db.get_item_details(item_state['listing_id'])
            item_name = item_state['item_name']
            properties = listing['properties']
            quantity = item_state['quantity']
            price = float(listing['price'])
            new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
            db.update_state(user_id, new_state)
            msg = 'Purchase successful!\n\n'
            msg += 'Item: %s\n' % item_name
            if properties:
                msg += 'Properties: %s\n' % ', '.join(json.loads(properties))
            msg += 'Quantity: %d\n' % quantity
            msg += 'Total price: $%.2f\n\n' % price * quantity
            msg += 'We will contact you soon for pickup details. Thank you for using Pipsqueak!'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            args = {'listingId': item_state['listing_id'], 'quantity': quantity, 'telegramId': user_id}
            db.bought_listing(args)
            seller_id = int(listing['sellerTelegramId'])
            seller_name = db.get_name(seller_id)
            user_name = update.callback_query.from_user.name
            msg = 'Purchase: %s (%d) has purchased from %s (%d) the following item:\n\n' % (user_name, user_id, seller_name, seller_id)
            msg += '%s (itemId: %d)\n' % (item_name, item_state['item_id'])
            if properties:
                msg += 'Properties: %s\n' % ', '.join(json.loads(properties))
            msg += 'Quantity: %d' % quantity
            msg += 'Total price: $%.2f\n\n' % price * quantity
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s (buyer)' % user_name, callback_data='forward_%d' % user_id)],
                                             [InlineKeyboardButton('Contact %s (seller)' % seller_name, callback_data='forward_%d' % seller_id)]])
            bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif data == 'marketplace':
        item_id = state['item_state']['item_id']
        state['state'] = 'marketplace'
        state['substate'] = 'seller'
        del state['item_state']['quantity']
        db.update_state(user_id, state)
        listings = db.get_listings(item_id)
        if listings:
            msg = 'We have these listings for %s:\n\n' % state['item_state']['item_name']
            keyboard = []
            for listing in listings:
                if int(listing['quantity']) > 0:
                    msg += 'ID: %d\n' % int(listing['listingId'])
                    msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
                    msg += 'Quantity available: %d\n' % int(listing['quantity'])
                    msg += 'Price: $%.2f\n\n' % float(listing['price'])
                    keyboard.append([InlineKeyboardButton('ID %d' % int(listing['listingId']), callback_data=str(listing['listingId']))])
            msg += 'Which one do you want to buy?'
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                             InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            stock(bot, update, state)
    elif data == 'store':
        listing_id = state['item_state']['listing_id']
        listing = db.get_listing_details(listing_id)
        if listing['properties']:
            state['state'] = 'buy'
            properties = listing['properties']
            state['item_state']['properties'] = properties
            del state['item_state']['listing_id']
            state['substate'] = 'quantity'
            db.update_state(user_id, state)
            item = db.get_item_details(state['item_state']['item_id'])
            if int(item['items'][properties]['quantity']) <= 0:
                stock(bot, update, state)
            else:
                msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                msg += 'Description: %s\n' % item['description']
                msg += 'Properties: %s\n\n' % ', '.join(json.loads(properties))
                if state['state'] != 'sell':
                    msg += 'We are selling at $%.2f each. ' % float(item['items'][properties]['price'])
                msg += 'How many do you want to %s?' % state['state']
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                                 [InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            state['state'] = 'buy'
            state['item_state']['properties'] = None
            del state['item_state']['listing_id']
            state['substate'] = 'quantity'
            db.update_state(user_id, state)
            item = db.get_item_details(state['item_state']['item_id'])
            if int(item['items']['quantity']) <= 0:
                stock(bot, update, state)
            else:
                msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                msg += 'Description: %s\n\n' % item['description']
                if state['state'] != 'sell':
                    msg += 'We are selling at $%.2f each. ' % float(item['items']['price'])
                msg += 'How many do you want to %s?' % state['state']
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                                 [InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        if state['state'] == 'buy':
            if state['item_state']['properties']:
                properties = state['item_state']['properties']
                del state['item_state']['quantity']
                state['substate'] = 'quantity'
                db.update_state(user_id, state)
                item = db.get_item_details(state['item_state']['item_id'])
                if int(item['items'][properties]['quantity']) <= 0:
                    stock(bot, update, state)
                else:
                    msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                    msg += 'Description: %s\n' % item['description']
                    msg += 'Properties: %s\n\n' % ', '.join(json.loads(properties))
                    msg += 'We are selling at $%.2f each. ' % float(item['items'][properties]['price'])
                    msg += 'How many do you want to %s?' % state['state']
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                                     [InlineKeyboardButton('<< back', callback_data='back'),
                                                      InlineKeyboardButton('/cancel', callback_data='cancel')]])
                    msg_id = update.callback_query.message.message_id
                    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                del state['item_state']['quantity']
                state['substate'] = 'quantity'
                db.update_state(user_id, state)
                item = db.get_item_details(state['item_state']['item_id'])
                if int(item['items']['quantity']) <= 0:
                    stock(bot, update, state)
                else:
                    msg = 'You want to %s %s\n' % (state['state'], state['item_state']['item_name'])
                    msg += 'Description: %s\n\n' % item['description']
                    msg += 'We are selling at $%.2f each. ' % float(item['items']['price'])
                    msg += 'How many do you want to %s?' % state['state']
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])],
                                                     [InlineKeyboardButton('<< back', callback_data='back'),
                                                      InlineKeyboardButton('/cancel', callback_data='cancel')]])
                    msg_id = update.callback_query.message.message_id
                    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        elif state['state'] == 'sell':
            item = db.get_item_details(state['item_state']['item_id'])
            if state['item_state']['properties']:
                price = float(item['items'][state['item_state']['properties']]['price'])
            else:
                price = float(item['items']['price'])
            quantity = state['item_state']['quantity']
            del state['item_state']['price']
            state['substate'] = 'price'
            db.update_state(user_id, state)
            msg = 'You want to sell %s\n' % state['item_state']['item_name']
            if state['item_state']['properties']:
                msg += 'Properties: %s\n' % ', '.join(json.loads(state['item_state']['properties']))
            msg += 'Quantity: %d\n\n' % quantity
            msg += 'We are currently selling this item at $%.2f each. How much do you want to sell for?' % price
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                              InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
        else:
            listing_id = state['item_state']['listing_id']
            state['substate'] = 'quantity'
            db.update_state(user_id, state)
            listing = db.get_listing_details(listing_id)
            if listing:
                msg = 'You want to buy %s\n' % listing['itemName']
                msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
                msg += 'Quantity available: %d\n' % int(listing['quantity'])
                msg += 'Price: $%.2f\n\n' % float(listing['price'])
                msg += 'How many do you want to buy?'
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                msg_id = update.callback_query.message.message_id
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                stock(bot, update, state)
    else:
        cancel(bot, update)


def stock(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    state['substate'] = 'stock'
    db.update_state(user_id, state)
    if state['state'] == 'buy':
        msg = 'Sorry, we are currently out of stock. Would you like to be notified when it becomes available?\n\n'
        msg += 'Alternatively, you can check the marketplace for student-listed items. '
        msg += 'Please note that we will not be issuing receipts for marketplace purchases.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='notify')],
                                         [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                         [InlineKeyboardButton('<< back', callback_data='back'),
                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
    else:
        msg = 'Sorry, no one is currently listing that item. Would you like to be notified when it becomes available?\n\n'
        msg += 'Alternatively, you can check the Pipsqueak store, '
        msg += 'where we will be issuing receipts for your purchases.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='notify')],
                                         [InlineKeyboardButton('Check store', callback_data='store')],
                                         [InlineKeyboardButton('<< back', callback_data='back'),
                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
    msg_id = update.callback_query.message.message_id
    bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def stock_callback_query(bot, update, state):
    global db
    global admin_id
    user_id = update.callback_query.from_user.id
    name = update.callback_query.from_user.name
    data = update.callback_query.data
    if data == 'notify':
        item_name = state['item_state']['item_name']
        db.add_request(user_id, name, item_name)
        new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
        db.update_state(user_id, new_state)
        msg = 'Got it! We will notify you as soon as the item becomes available. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        msg = 'Notify: %s (%d) wants to be notified for %s' % (name, user_id, item_name)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif data == 'marketplace':
        item_id = state['item_state']['item_id']
        item_category = state['item_state']['category']
        page = state['item_state']['page']
        item_name = state['item_state']['item_name']
        state['item_state'] = {'category': item_category, 'page': page, 'item_id': item_id, 'item_name': item_name}
        state['substate'] = 'seller'
        db.update_state(user_id, state)
        listings = db.get_listings(item_id)
        if listings:
            msg = 'We have these listings for %s:\n\n' % state['item_state']['item_name']
            keyboard = []
            for listing in listings:
                if int(listing['quantity']) > 0:
                    msg += 'ID: %d\n' % int(listing['listingId'])
                    msg += 'Properties: %s\n' % ', '.join(json.loads(listing['properties']))
                    msg += 'Quantity available: %d\n' % int(listing['quantity'])
                    msg += 'Price: $%.2f\n\n' % float(listing['price'])
                    keyboard.append([InlineKeyboardButton('ID %d' % int(listing['listingId']), callback_data=str(listing['listingId']))])
            msg += 'Which one do you want to buy?'
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                             InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            stock(bot, update, state)
    elif data == 'store':
        item_id = state['item_state']['item_id']
        item = db.get_item_details(item_id)
        options = item['options']
        if options is None or options == 'null':
            item_category = state['item_state']['category']
            page = state['item_state']['page']
            state['substate'] = 'item'
            state['item_state'] = {'category': item_category, 'page': page}
            db.update_state(user_id, state)
            items = db.get_items(item_category, page)
            msg = 'What %s do you want to buy?' % item_category
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                             InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            options_list = [list(option.keys())[0] for option in options]
            state['item_state']['item_id'] = item_id
            state['item_state']['item_name'] = item['itemName']
            state['item_state']['options'] = options_list
            state['item_state']['index'] = 0
            state['substate'] = 'options'
            db.update_state(user_id, state)
            msg = 'You want to buy %s\n' % state['item_state']['item_name']
            msg += 'Description: %s\n\n' % item['description']
            msg += 'What %s do you want to %s?' % (options_list[0].lower(), state['state'])
            keyboard = [[InlineKeyboardButton('See image', callback_data='img ' + item['imageUrl'])]]
            for option in options[0][options_list[0]]:
                keyboard.append([InlineKeyboardButton(option, callback_data=option)])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                             InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        item_category = state['item_state']['category']
        page = state['item_state']['page']
        state['substate'] = 'item'
        state['item_state'] = {'category': item_category, 'page': page}
        db.update_state(user_id, state)
        items = db.get_items(item_category, page)
        msg = 'What %s do you want to buy?' % item_category
        keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
        keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                         InlineKeyboardButton('Next >>', callback_data='next')])
        keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='request')])
        keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


# Request function
def request(bot, update):
    global db
    user_id, state = precheck(update)
    state['substate'] = 'request'
    db.update_state(user_id, state)
    if state['state'] == 'sell':
        msg = 'We limit the items we sell on Pipsqueak to make sure every item we sell does not go against company and community policies. For example, you can\'t list items that you can get from the Fab Lab for free.\n\n'
        msg += 'If you believe your item should fit the criteria, you can request to list your item, and we will review your item beforehand.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Request listing', callback_data='true')],
                                         [InlineKeyboardButton('<< back', callback_data='back'),
                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif state['state'] == 'home':
        msg = 'You can request for items that we don\'t currently have. If it\'s feasible, we might decide to stock that item in our inventory.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Request item', callback_data='true')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)
    else:
        msg = 'You can request for items that we don\'t currently have. If it\'s feasible, we might decide to stock that item in our inventory.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Request item', callback_data='true')],
                                         [InlineKeyboardButton('<< back', callback_data='back'),
                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def request_callback_query(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    if data == 'true':
        msg = 'Alright, what item do you want to be %s?' % 'sell' if state['state'] == 'sell' else 'buy'
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    elif data == 'back':
        state['substate'] = 'category'
        state['item_state'] = None
        db.update_state(user_id, state)
        msg = 'What category of items do you want to %s?' % 'sell' if state['state'] == 'sell' else 'buy'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='stationery')],
                                         [InlineKeyboardButton('IC chips', callback_data='ICs')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='request')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def request_message(bot, update, state):
    global db
    global admins
    user_id = update.message.from_user.id
    name = update.message.from_user.name
    text = update.message.text
    if state['state'] == 'sell':
        msg = 'Approval: %s (%d) wants to list %s' % (name, user_id, text)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Approve', callback_data='approve_%d_%s' % (user_id, text)),
                                          InlineKeyboardButton('Reject', callback_data='reject_%d_%s' % (user_id, text))],
                                         [InlineKeyboardButton('Contact %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
        msg = 'Got it! We will notify you as soon as an admin reviews your listing. Thank you for using Pipsqueak!'
    else:
        db.add_request(user_id, name, text)
        msg = 'Request: %s (%d) wants to request %s' % (name, user_id, text)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
        msg = 'Got it! We will notify you as soon as the item becomes available. Thank you for using Pipsqueak!'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
    new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
    db.update_state(user_id, new_state)
    bot.send_message(user_id, msg, reply_markup=keyboard)


# Food functions
def food(bot, update):
    global db
    user_id, state = precheck(update)
    if state['state'] == 'home':
        if state['substate'] == 'home':
            state['substate'] = 'food1'
            db.update_state(user_id, state)
            msg = 'Sorry, we are a parts marketplace. We\'re totally not selling food.'
            bot.send_message(user_id, msg)
        elif state['substate'] == 'food1':
            state['substate'] = 'food2'
            db.update_state(user_id, state)
            msg = 'Dude, seriously. We can\'t be selling food here. We are a PARTS marketplace.'
            bot.send_message(user_id, msg)
        elif state['substate'] == 'food2':
            state = {'state': 'food', 'substate': 'item', 'item_state': {'category': 'food'}}
            db.update_state(user_id, state)
            msg = 'Sigh, fine... What do you want?'
            foods = db.get_food()
            keyboard = [[InlineKeyboardButton(item[1], callback_data=str(item[0]))] for item in foods]
            keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.send_message(user_id, msg, reply_markup=keyboard)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
        bot.send_message(user_id, msg)


def food_item(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'cancel':
        cancel(bot, update)
    else:
        item_id = int(data)
        item = db.get_food(item_id)
        item_name = item[1]
        quantity = item[2]
        if quantity > 0:
            price = round(item[3], 2)
            state['substate'] = 'quantity'
            state['item_state']['item_id'] = item_id
            db.update_state(user_id, state)
            msg = 'We have %s for $%.2f each. How many do you want to buy?' % (item_name, price)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                              InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            query_id = update.callback_query.id
            msg = 'Sorry, we\'re out of stock!'
            bot.answer_callback_query(query_id, msg)


def food_quantity_callback_query(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'cancel':
        cancel(bot, update)
    else:
        state['substate'] = 'item'
        state['item_state'] = {'category': 'food'}
        db.update_state(user_id, state)
        msg = 'What do you want?'
        foods = db.get_food()
        keyboard = [[InlineKeyboardButton(item[1], callback_data=str(item[0]))] for item in foods]
        keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def food_quantity_message(bot, update, state):
    global db
    user_id = update.message.from_user.id
    item_id = state['item_state']['item_id']
    item = db.get_food(item_id)
    item_name = item[1]
    in_stock = int(item[2])
    price = round(float(item[3]), 2)
    try:
        quantity = int(update.message.text)
        if quantity < 0:
            msg = 'That\'s not a valid quantity. Please try again.'
            bot.send_message(user_id, msg)
        elif quantity > in_stock:
            msg = 'That\'s more than we have in stock right now. Please try again.'
            bot.send_message(user_id, msg)
        else:
            state['item_state']['quantity'] = quantity
            state['substate'] = 'confirm'
            db.update_state(user_id, state)
            msg = 'You want to buy %s\n' % item_name
            msg += 'Quantity: %d\n' % quantity
            if quantity > 1:
                msg += 'Price: $%.2f each, $%.2f total\n\n' % (price, price * quantity)
            else:
                msg += 'Price: $%.2f\n\n' % price
            msg += 'Is this correct?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Confirm', callback_data='confirm')],
                                             [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid quantity. Please try again.'
        bot.send_message(user_id, msg)


def food_confirm(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'back':
        item_id = state['item_state']['item_id']
        state['substate'] = 'quantity'
        del state['item_state']['quantity']
        item = db.get_food(item_id)
        item_name = item[1]
        price = round(item[3], 2)
        db.update_state(user_id, state)
        msg = 'We have %s for $%.2f each. How many do you want to buy?' % (item_name, price)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                          InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        global admin_id
        item_id = state['item_state']['item_id']
        item = db.get_food(item_id)
        item_name = item[1]
        quantity = state['item_state']['quantity']
        price = round(float(item[3]), 2)
        new_state = {'state': 'home', 'substate': 'home', 'item_state': None}
        db.update_state(user_id, new_state)
        msg = 'Purchase successful: %s! We will contact you soon for pickup details. Thank you for using Pipsqueak!' % item_name
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        name = update.callback_query.from_user.name
        msg = 'Purchase: %s (%d) purchased %s\n' % (name, user_id, item_name)
        msg += 'Quantity: %d\n' % quantity
        if quantity > 1:
            msg += 'Price: $%.2f each, $%.2f total' % (price, price * quantity)
        else:
            msg += 'Price: $%.2f' % price
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)


# Handlers
def message_handler(bot, update):
    user_id, state = precheck(update)
    if state['state'] == 'forward':
        if state['substate'] is None:
            forward_connect(bot, update, state)
        else:
            text = update.message.text
            target_id = state['substate']
            bot.send_message(target_id, text)
    elif state['state'] == 'broadcast':
        broadcast_message(bot, update)
    elif state['state'] == 'feedback':
        global admin_id
        db.add_feedback(user_id, update.message.from_user.name, update.message.text)
        bot.send_message(admin_id, update.message.text)
        msg = 'Got it! Anything else you want to feedback to us? Please use /done when you\'re finished!'
        bot.send_message(user_id, msg)
    elif state['state'] == 'food' and state['substate'] == 'quantity':
        food_quantity_message(bot, update, state)
    elif state['substate'] == 'quantity':
        quantity_message(bot, update, state)
    elif state['substate'] == 'price':
        price_message(bot, update, state)
    else:
        msg = 'Please use /start to begin trading!'
        bot.send_message(user_id, msg)


def callback_query_handler(bot, update):
    user_id, state = precheck(update)
    text = update.callback_query.message.text
    if text.startswith('An admin is connecting to you. '):
        target_id = int(update.callback_query.data.split('_')[1])
        new_state = {'state': 'forward', 'substate': target_id, 'item_state': None}
        db.update_state(user_id, new_state)
        msg_id = update.callback_query.message.message_id
        msg = 'You are now connected to an admin.'
        bot.edit_message_text(msg, user_id, msg_id)
        msg = '%s is now connected.' % update.callback_query.from_user.name
        bot.send_message(target_id, msg)
    elif text.startswith('Help: ') or text.startswith('Purchase: ') or text.startswith('Listing: ') or text.startswith('Request: ') or text.startswith('Notify: '):
        forward_connect(bot, update, state)
    elif text.startswith('Approval: '):
        data = update.callback_query.data
        if data.startswith('forward_'):
            forward_connect(bot, update, state)
        else:
            review_request(bot, update, data)
    elif state['state'] == 'home':
        data = update.callback_query.data
        if data == 'buy':
            buy(bot, update)
        elif data == 'sell':
            sell(bot, update)
        elif data == 'feedback':
            feedback(bot, update)
        elif data == 'help':
            help_command(bot, update)
        else:
            query_id = update.callback_query.id
            msg = 'Please use /start to begin trading!'
            bot.answer_callback_query(query_id, msg)
    elif state['state'] == 'food':
        if state['substate'] == 'item':
            food_item(bot, update, state)
        elif state['substate'] == 'quantity':
            food_quantity_callback_query(bot, update, state)
        elif state['substate'] == 'confirm':
            food_confirm(bot, update, state)
    elif state['substate'] == 'category':
        category(bot, update, state)
    elif state['substate'] == 'item':
        choose_item(bot, update, state)
    elif state['substate'] == 'seller':
        seller(bot, update, state)
    elif state['substate'] == 'options':
        choose_options(bot, update, state)
    elif state['substate'] == 'quantity':
        quantity_callback_query(bot, update, state)
    elif state['substate'] == 'price':
        price_callback_query(bot, update, state)
    elif state['substate'] == 'confirm':
        confirm(bot, update, state)
    elif state['substate'] == 'stock':
        stock_callback_query(bot, update, state)
    else:
        query_id = update.callback_query.id
        msg = 'Please use /start to begin trading!'
        bot.answer_callback_query(query_id, msg)


# Main
def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('buy', buy))
    dispatcher.add_handler(CommandHandler('sell', sell))
    dispatcher.add_handler(CommandHandler('request', request))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CommandHandler('done', done))
    dispatcher.add_handler(CommandHandler('feedback', feedback))
    dispatcher.add_handler(CommandHandler('food', food))
    dispatcher.add_handler(CommandHandler('_cancel', force_cancel))
    dispatcher.add_handler(CommandHandler('_state', force_state))
    dispatcher.add_handler(CommandHandler('_forward', admin_forward))
    dispatcher.add_handler(CommandHandler('_broadcast', broadcast_command))

    dispatcher.add_handler(MessageHandler(filters.Filters.text, message_handler))

    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    admin_id = -1001312124809
    admins = (111914928, 230937024, 255484909, 42010966)
    main()
