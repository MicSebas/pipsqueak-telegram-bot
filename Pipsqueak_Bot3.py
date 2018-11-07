import telegram
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from Database import Database
import json

TOKEN = '666724238:AAF2SyvjZbui0VMbPOlG3op2jgMQFVFM_yg'
PORT = int(os.environ.get('PORT', '5000'))
BOT = telegram.Bot(token=TOKEN)
BOT.setWebhook(url='https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)


def pre_check(bot, update):
    global db
    global admins
    if update.callback_query is not None:
        user_id = update.callback_query.from_user.id
        name = update.callback_query.from_user.name
    else:
        user_id = update.message.from_user.id
        name = update.message.from_user.name
    if user_id in admins:
        users_list = db.get_users()
        if user_id not in users_list:
            db.add_new_user(user_id, name, 'home')
            return True
        else:
            if db.get_state(user_id).startswith('home'):
                return True
            else:
                msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
                bot.send_message(user_id, msg)
                return False


# General Commands
def start(bot, update):
    if pre_check(bot, update):
        global db
        user_id = update.message.from_user.id
        db.update_state(user_id, 'home')
        msg = 'Hello, %s! Welcome to Pipsqueak, the first online parts marketplace in SUTD! My name is Mary Pippins. How can I help you today?' % update.message.from_user.first_name
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('I want to /buy things', callback_data='buy')],
                                         [InlineKeyboardButton('I want to /sell things', callback_data='sell')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)


def cancel(bot, update):
    global db
    if update.callback_query is not None:
        user_id = update.callback_query.from_user.id
        name = update.callback_query.from_user.name
    else:
        user_id = update.message.from_user.id
        name = update.message.from_user.name
    users_list = db.get_users()
    if user_id not in users_list:
        db.add_new_user(user_id, name, 'home')
    state = db.get_state(user_id)
    if state.startswith('home'):
        if state != 'home':
            db.update_state(user_id, 'home')
        msg = 'You\'re not in the middle of any operation. Please use /start to begin trading.'
        bot.send_message(user_id, msg)
    elif state.startswith('food'):
        db.update_state(user_id, 'home')
        msg = '...'
        if update.callback_query is not None:
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        else:
            bot.send_message(user_id, msg, reply_markup=None)
    else:
        msg = 'Operation cancelled. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        db.update_state(user_id, 'home')
        if update.callback_query is not None:
            msg_id = update.callback_query.message.message_id
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            bot.send_message(user_id, msg, reply_markup=keyboard)


def force_cancel(bot, update):
    global db
    user_id = update.message.from_user.id
    db.update_state(user_id, 'home')
    msg = 'Back to home state'
    bot.send_message(user_id, msg)


def done(bot, update):
    global db
    user_id = update.message.from_user.id
    name = update.message.from_user.name
    users_list = db.get_users()
    if user_id not in users_list:
        db.add_new_user(user_id, name, 'home')
    state = db.get_state(user_id)
    if state == 'home':
        msg = 'You\'re not in the middle of any operation. Please use /start to begin trading.'
        bot.send_message(user_id, msg)
    else:
        global admin_id
        global admins
        if state == 'feedback':
            msg = 'End of feedback from %s' % update.message.from_user.name
            bot.send_message(admin_id, msg)
            msg = 'Your feedback has been received. Thank you for using Pipsqueak!'
            db.update_state(user_id, 'home')
            bot.send_message(user_id, msg)
        elif state.startswith('forward_'):
            target_id = int(state.split('_')[1])
            db.update_state(target_id, 'home')
            db.update_state(user_id, 'home')
            msg = 'You are no longer connected. Thank you for using Pipsqueak!'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
            if user_id not in admins:
                bot.send_message(user_id, msg, reply_markup=keyboard)
                bot.send_message(target_id, msg)
            else:
                bot.send_message(user_id, msg)
                bot.send_message(target_id, msg, reply_markup=keyboard)
        else:
            msg = 'There\'s a time and place for everything. But now is not the time for this.'
            db.update_state(user_id, 'home')
            bot.send_message(user_id, msg)


def help_command(bot, update):
    if pre_check(bot, update):
        global db
        user_id = update.message.from_user.id
        db.update_state(user_id, 'help')
        msg = 'We can connect you to an admin to help assist you better. Do you want to proceed?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='yes'), InlineKeyboardButton('No', callback_data='no')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)


def help_confirm(bot, update):
    global db
    global admin_id
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    db.update_state(user_id, 'home')
    if data == 'yes':
        msg = 'We are connecting you to an admin. Please hold.'
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        name = update.callback_query.from_user.name
        msg = 'Help: %s (%d) is trying to connect to an admin.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect to %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    else:
        cancel(bot, update)


def feedback(bot, update):
    global db
    global admin_id
    if pre_check(bot, update):
        if update.callback_query is not None:
            user_id = update.callback_query.from_user.id
            name = update.callback_query.from_user.name
            msg_id = update.callback_query.message.message_id
            bot.edit_message_reply_markup(user_id, msg_id, reply_markup=None)
        else:
            user_id = update.message.from_user.id
            name = update.message.from_user.name
        db.update_state(user_id, 'feedback')
        msg = 'Your feedback is very valuable to us! Please tell us how we can improve to serve you better, be as specific as you like!\n\nUse /done when you\'re finished.'
        bot.send_message(user_id, msg)
        msg = 'Feedback from %s:' % name
        bot.send_message(admin_id, msg)


def request(bot, update):
    global db
    if update.callback_query is not None:
        user_id = update.callback_query.from_user.id
        msg_id = update.callback_query.message.message_id
        data = update.callback_query.data
        if data == 'true':
            db.update_state(user_id, 'request_item')
            msg = 'Alright, what item do you want to be notified about?'
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
        elif data == 'buy':
            buy(bot, update)
        elif data == 'marketplace':
            marketplace(bot, update)
        else:
            cancel(bot, update)
    else:
        if pre_check(bot, update):
            user_id = update.message.from_user.id
            msg = 'You can request to be notified when an item becomes available. What item do you want to be notified about?'
            bot.send_message(user_id, msg)


def request_item(bot, update):
    global db
    user_id = update.message.from_user.id
    msg = 'Got it! We will notify you as soon as the item becomes available. Thank you for using Pipsqueak!'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
    db.update_state(user_id, 'home')
    bot.send_message(user_id, msg, reply_markup=keyboard)


# Admin functions
def connect(bot, update):
    global db
    global admins
    global admin_id
    user_id = update.callback_query.from_user.id
    if user_id in admins:
        admin_name = update.callback_query.from_user.name
        data = update.callback_query.data
        target_id = int(data.split('_')[1])
        target_name = db.get_name(target_id)
        msg = '%s is connecting to %s' % (admin_name, target_name)
        bot.send_message(admin_id, msg)
        db.update_state(user_id, data)
        msg = 'Waiting to connect to %s' % target_name
        bot.send_message(user_id, msg)
        msg = 'An admin is connecting to you. Do note that connecting to an admin will override your current operations.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Connect now', callback_data='forward_%d' % user_id)]])
        bot.send_message(target_id, msg, reply_markup=keyboard)
    else:
        query_id = update.callback_query.id
        msg = 'You are not authorized to use this function!'
        bot.answer_callback_query(query_id, msg)


def review_request(bot, update):
    global db
    global admins
    global admin_id
    user_id = update.callback_query.from_user.id
    if user_id in admins:
        data = update.callback_query.data
        # TODO: Fill in review function
        if data == 'approve':
            pass
        else:
            pass
    else:
        query_id = update.callback_query.id
        msg = 'You are not authorized to use this function!'
        bot.answer_callback_query(query_id, msg)


# Buy functions
def buy(bot, update):
    if pre_check(bot, update):
        global db
        msg = 'What category of items do you want to buy?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='Materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='Electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='Adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='Stationery')],
                                         [InlineKeyboardButton('Amenities', callback_data='Amenities')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='none')]])
        if update.callback_query is not None:
            user_id = update.callback_query.from_user.id
            msg_id = update.callback_query.message.message_id
            db.update_state(user_id, 'buy')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            user_id = update.message.from_user.id
            db.update_state(user_id, 'buy')
            bot.send_message(user_id, msg, reply_markup=keyboard)


def buy_category(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'none':
        db.update_state(user_id, 'buy_request')
        msg = 'We\'re sorry you couldn\'t find what you want. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                         [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        args = {'category': data, 'page': 0}
        items = db.get_items(args)
        if items:
            db.update_state(user_id, 'buy_%s_0_item' % data)
            msg = 'What %s do you want to buy?' % data.lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            query_id = update.callback_query.id
            msg = 'There are currently no %s in stock!' % data.lower()
            bot.answer_callback_query(query_id, msg)


def buy_item(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'none':
        db.update_state(user_id, 'buy_request')
        msg = 'We\'re sorry you couldn\'t find what you want. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                         [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'category':
        db.update_state(user_id, 'home')
        buy(bot, update)
    elif data == 'prev':
        state = db.get_state(user_id)
        state_list = state.split('_')
        page = int(state_list[2])
        if page == 0:
            callback_query_id = update.callback_query.id
            msg = 'There is no previous page!'
            bot.answer_callback_query(callback_query_id, msg)
        else:
            db.update_state(user_id, 'buy_%s_%d_item' % (state_list[1], page - 1))
            args = {'category': state_list[1], 'page': page - 1}
            items = db.get_items(args)
            msg = 'What %s do you want to buy?' % state_list[1].lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'next':
        state = db.get_state(user_id)
        state_list = state.split('_')
        page = int(state_list[2])
        args = {'category': state_list[1], 'page': page + 1}
        items = db.get_items(args)
        if items:
            db.update_state(user_id, 'buy_%s_%d_item' % (state_list[1], page + 1))
            msg = 'What %s do you want to buy?' % state_list[1].lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            callback_query_id = update.callback_query.id
            msg = 'There is no next page!'
            bot.answer_callback_query(callback_query_id, msg)
    else:
        item_id = int(data)
        category = db.get_state(user_id).split('_')[1]
        item = db.get_items({'item': item_id})
        options = item['options']
        print(options)
        print(type(options))
        if options:
            option_state = [list(d.keys())[0] for d in options]
            db.update_state(user_id, 'buy_%s_%d_%s_options' % (category, item_id, json.dumps(option_state)))
            msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
            keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
            keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            quantity = int(item['items']['quantity'])
            if quantity > 0:
                db.update_state(user_id, 'buy_%s_%d_null_quantity' % (db.get_state(user_id).split('_')[1], item_id))
                msg = 'You want to buy %s' % item['itemName']
                msg += '\n\nWe currently have %d in stock. How many do you want to buy?' % quantity
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                db.update_state(user_id, 'buy_%s_%d_nostock' % (db.get_state(user_id).split('_')[1], item_id))
                msg = 'I\'m sorry, but we currently don\'t have that item in stock. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                                 [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                                 [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def buy_options(bot, update, item_id, options_state):
    global db
    print(options_state)
    print(type(options_state))
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == '0_back':
        category = db.get_state(user_id).split('_')[1]
        items = db.get_items({'category': category, 'page': 0})
        db.update_state(user_id, 'buy_%s_0_item' % category)
        msg = 'What %s do you want to buy?' % category.lower()
        keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
        keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
        keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
        keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        state = db.get_state(user_id)
        item_id = int(state.split('_')[2])
        item = db.get_items({'item': item_id})
        options = item['options']
        option_state = [list(d.keys())[0] for d in options]
        db.update_state(user_id, 'buy_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(option_state)))
        msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
        keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
        keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'none':
        db.update_state(user_id, 'buy_request')
        msg = 'We\'re sorry you couldn\'t find what you want. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                         [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        data_l = data.split('_')
        i = int(data_l[0])
        option = data_l[1]
        options_state[i] = option
        if i < len(options_state) - 1:
            item = db.get_items({'item': item_id})
            options = item['options']
            d = options[i + 1]
            k = list(d.keys())[0]
            db.update_state(user_id, 'buy_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(options_state)))
            msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), k.lower())
            keyboard = [[InlineKeyboardButton(choice, callback_data='%d_%s' % (i + 1, choice))] for choice in d[k]]
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            item = db.get_items({'item': item_id})
            options_state.reverse()
            options_state = json.dumps(options_state, separators=(',', ':'))  # TODO: Delete this line later and complain to Ray
            quantity = int(item['items'][options_state]['quantity'])
            if quantity > 0:
                db.update_state(user_id, 'buy_%s_%d_%s_quantity' % (db.get_state(user_id).split('_')[1], item_id, options_state))
                msg = 'You want to buy %s: ' % item['itemName']
                msg += ', '.join(json.loads(options_state))
                msg += '\n\nWe currently have %d in stock. How many do you want to buy?' % quantity
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                db.update_state(user_id, 'buy_%s_%d_nostock' % (db.get_state(user_id).split('_')[1], item_id))
                msg = 'I\'m sorry, but we currently don\'t have that item in stock. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                                 [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                                 [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def buy_nostock(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state_list = state.split('_')
    item_id = int(state_list[2])
    data = update.callback_query.data
    if data == 'true':
        global admin_id
        db.update_state(user_id, 'home')
        msg = 'Got it! We will notify you as soon as the item becomes available. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        name = update.callback_query.from_user.name
        item = db.get_items({'item': item_id})['itemName']
        msg = '%s (%d) has requested to be notified for the following item: %s.' % (name, user_id, item)
        bot.send_message(admin_id, msg)
    elif data == 'marketplace':
        category = state_list[1]
        item = json.loads(db.get_items_marketplace(item_id=item_id))
        options = item['options']
        option_state = [list(d.keys())[0] for d in options]
        db.update_state(user_id, 'marketplace_%s_%d_%s_options' % (category, item_id, json.dumps(option_state)))
        msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
        keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
        keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        item = db.get_items({'item': item_id})
        options = item['options']
        option_state = [list(d.keys())[0] for d in options]
        db.update_state(user_id, 'buy_%s_%d_%s_options' % (state_list[1], item_id, json.dumps(option_state)))
        msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
        keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
        keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def buy_quantity_callback_query(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state = db.get_state(user_id)
    data = update.callback_query.data
    if data == 'back':
        state_list = state.split('_')
        category = state_list[1]
        item_id = int(state_list[2])
        item = db.get_items({'item': item_id})
        options = item['options']
        if options:
            option_state = [list(d.keys())[0] for d in options]
            db.update_state(user_id, 'buy_%s_%d_%s_options' % (category, item_id, json.dumps(option_state)))
            msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
            keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
            keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            items = db.get_items({'category': category, 'page': 0})
            db.update_state(user_id, 'buy_%s_0_item' % category)
            msg = 'What %s do you want to buy?' % category.lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def buy_quantity_message(bot, update):
    global db
    user_id = update.message.from_user.id
    try:
        quantity = int(update.message.text)
        state = db.get_state(user_id)
        state_list = state.split('_')
        item_id = int(state_list[2])
        options = state_list[3]
        # try:
        #     options = json.loads(state_list[3])
        # except json.decoder.JSONDecodeError:
        #     options = None
        item = db.get_items({'item': item_id})
        print('hi')
        print(item)
        print(options)
        if options != 'null':
            # options = json.dumps(options)  # TODO: Ray Y U do dis
            stock = int(item['items'][options]['quantity'])
        else:
            stock = int(item['items']['quantity'])
        if quantity <= 0:
            msg = 'That\'s not a valid quantity. Please try again.'
            bot.send_message(user_id, msg)
        elif quantity > stock:
            msg = 'That\'s more than the stock we currently have. Please try again.'
            bot.send_message(user_id, msg)
        else:
            db.update_state(user_id, '_'.join(state_list[:-1]) + '_%d_confirm' % quantity)
            try:
                if options != 'null':
                    price = float(item['items'][options]['price'])
                else:
                    price = float(item['items']['price'])
            except ValueError:
                if options:
                    price = float(item['items'][options]['price'][1:])
                else:
                    price = float(item['items']['price'][1:])
            msg = 'You want to buy %s' % item['itemName']
            if options != 'null':
                msg += ': ' + ', '.join(json.loads(options))
            msg += '. We are currently selling this item for $%.2f' % price
            if quantity > 1:
                msg += ' each, $%.2f total for %d items.\n\n' % (quantity * price, quantity)
            else:
                msg += '.\n\n'
            msg += 'Alternatively, you can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases.\n\nWould you like to buy now?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Buy now', callback_data='confirm')],
                                             [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                             [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid quantity. Please try again.'
        bot.send_message(user_id, msg)


def buy_confirm(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state_list = state.split('_')
    category = state_list[1]
    item_id = int(state_list[2])
    options = state_list[3]
    # try:
    #     options = json.loads(state_list[3])
    # except json.decoder.JSONDecodeError:
    #     options = None
    quantity = int(state_list[4])
    data = update.callback_query.data
    print(options)
    print(type(options))
    if data == 'confirm':
        global admin_id
        db.update_state(user_id, 'home')
        item = db.get_items({'item': item_id})
        print(item)
        if options != 'null':
            msg = 'Purchase successful!\n\n%s: ' % item['itemName']
            msg += ', '.join(json.loads(options))
            msg += '\nQuantity: %d\nTotal price: $%.2f\n\n' % (quantity, quantity * float(item['items'][options]['price']))
            msg += 'We will contact you soon for pickup details. Thank you for using Pipsqueak!'
        else:
            msg = 'Purchase successful: %s!\n\n' % item['itemName']
            msg += 'Quantity: %d\nTotal price: $%.2f\n\n' % (quantity, quantity * float(item['items']['price']))
            msg += 'We will contact you soon for pickup details. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        args = {'item': item_id, 'quantity': quantity, 'telegramId': user_id}
        if options != 'null':
            args['properties'] = options
        text = db.bought_item(args)
        text_list = text.split('\n')
        msg = text_list[1]
        url = 'phpstack-212261-643485.cloudwaysapps.com/logon/register?telegramId=' + str(user_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Complete registration', url=url)]])
        bot.send_message(user_id, msg, reply_markup=keyboard)
        msg = 'Purchase: %s (%d) has purchased the following item: %s (itemId: %d) (quantity: %d)' % (update.callback_query.from_user.name, user_id, item['itemName'], item_id, quantity)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % update.callback_query.from_user.name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif data == 'marketplace':
        item = json.loads(db.get_items_marketplace(item_id=item_id))
        options = item['options']
        option_state = [list(d.keys())[0] for d in options]
        db.update_state(user_id, 'marketplace_%s_%d_%s_options' % (category, item_id, json.dumps(option_state)))
        msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
        keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
        keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        item = db.get_items({'item': item_id})
        db.update_state(user_id, 'buy_%s_%d_%s_quantity' % (category, item_id, options))
        msg = 'You want to buy %s' % item['itemName']
        if options != 'null':
            msg += ': ' + ', '.join(json.loads(options))
            stock = item['items'][options]['quantity']
        else:
            stock = item['items']['quantity']
        msg += '\n\nWe currently have %d in stock. How many do you want to buy?' % stock
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


# Sell functions
def sell(bot, update):
    if pre_check(bot, update):
        global db
        msg = 'What category of items do you want to sell?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='Materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='Electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='Adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='Stationery')],
                                         [InlineKeyboardButton('Amenities', callback_data='Amenities')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='none')]])
        if update.callback_query is not None:
            user_id = update.callback_query.from_user.id
            msg_id = update.callback_query.message.message_id
            db.update_state(user_id, 'sell')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            user_id = update.message.from_user.id
            db.update_state(user_id, 'sell')
            bot.send_message(user_id, msg, reply_markup=keyboard)


def sell_category(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data != 'none':
        items = db.get_items({'category': data, 'page': 0})
        db.update_state(user_id, 'sell_%s_0_item' % data)
        msg = 'What %s do you want to sell?' % data.lower()
        keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
        keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
        keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
        keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        db.update_state(user_id, 'sell_request')
        msg = 'We limit the items we sell on Pipsqueak to make sure every item we sell does not go against company and community policies. For example, you can\'t list items that you can get from the Fab Lab for free.\n\n'
        msg += 'If you believe your item should fit the criteria, you can request to list your item, and we will review your item beforehand.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Request listing', callback_data='true')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def sell_item(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'none':
        db.update_state(user_id, 'sell_request')
        msg = 'We limit the items we sell on Pipsqueak to make sure every item we sell does not go against company and community policies. For example, you can\'t list items that you can get from the Fab Lab for free.\n\n'
        msg += 'If you believe your item should fit the criteria, you can request to list your item, and we will review your item beforehand.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Request listing', callback_data='true')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'category':
        db.update_state(user_id, 'home')
        sell(bot, update)
    elif data == 'prev':
        state = db.get_state(user_id)
        state_list = state.split('_')
        page = int(state_list[2])
        if state_list[2] == 0:
            callback_query_id = update.callback_query.id
            msg = 'There is no previous page!'
            bot.answer_callback_query(callback_query_id, msg)
        else:
            db.update_state(user_id, 'sell_%s_%d_item' % (state_list[1], page - 1))
            items = db.get_items({'category': state_list[1], 'page': page - 1})
            msg = 'What %s do you want to sell?' % state_list[1].lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=item['itemId'])] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'next':
        state = db.get_state(user_id)
        state_list = state.split('_')
        page = int(state_list[2])
        items = db.get_items({'category': state_list[1], 'page': page + 1})
        if items:
            db.update_state(user_id, 'sell_%s_%d_item' % (state_list[1], page + 1))
            msg = 'What %s do you want to sell?' % state_list[1].lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=item['itemId'])] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            callback_query_id = update.callback_query.id
            msg = 'There is no next page!'
            bot.answer_callback_query(callback_query_id, msg)
    else:
        item_id = int(data)
        category = db.get_state(user_id).split('_')[1]
        item = db.get_items({'item': item_id})
        options = item['options']
        if options:
            option_state = [list(d.keys())[0] for d in options]
            db.update_state(user_id, 'sell_%s_%d_%s_options' % (category, item_id, json.dumps(option_state)))
            msg = 'Selling a %s\n\nWhat %s is it?' % (item['itemName'].lower(), option_state[0].lower())
            keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
            keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            item = db.get_items({'item': item_id})
            db.update_state(user_id, 'sell_%s_%d_null_quantity' % (db.get_state(user_id).split('_')[1], item_id))
            msg = 'You want to sell %s' % item['itemName']
            msg += '\n\nHow many do you want to sell?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def sell_options(bot, update, item_id, options_state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == '0_back':
        category = db.get_state(user_id).split('_')[1]
        items = db.get_items({'category': category, 'page': 0})
        db.update_state(user_id, 'sell_%s_0_item' % category)
        msg = 'What %s do you want to sell?' % category.lower()
        keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
        keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
                         InlineKeyboardButton('Next >>', callback_data='next')])
        keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
        keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        state = db.get_state(user_id)
        item_id = int(state.split('_')[2])
        item = db.get_items({'item': item_id})
        options = item['options']
        option_state = [list(d.keys())[0] for d in options]
        db.update_state(user_id, 'sell_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(option_state)))
        msg = 'Selling a %s\n\nWhat %s is it?' % (item['itemName'].lower(), option_state[0].lower())
        keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
        keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'none':
        db.update_state(user_id, 'sell_request')
        msg = 'We limit the items we sell on Pipsqueak to make sure every item we sell does not go against company and community policies. For example, you can\'t list items that you can get from the Fab Lab for free.\n\n'
        msg += 'If you believe your item should fit the criteria, you can request to list your item, and we will review your item beforehand.'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Request listing', callback_data='true')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        data_l = data.split('_')
        i = int(data_l[0])
        option = data_l[1]
        options_state[i] = option
        if i < len(options_state) - 1:
            item = db.get_items({'item': item_id})
            options = item['options']
            d = options[i + 1]
            k = list(d.keys())[0]
            db.update_state(user_id, 'sell_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(options_state)))
            msg = 'Selling a %s\n\nWhat %s is it?' % (item['itemName'].lower(), k.lower())
            keyboard = [[InlineKeyboardButton(choice, callback_data='%d_%s' % (i + 1, choice))] for choice in d[k]]
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            item = db.get_items({'item': item_id})
            options_state.reverse()  # TODO: Ray Y U Do Dis
            db.update_state(user_id, 'sell_%s_%d_%s_quantity' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(options_state, separators=(',', ':'))))
            msg = 'You want to sell %s: ' % item['itemName']
            msg += ', '.join(options_state)
            msg += '\n\nHow many do you want to sell?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def sell_quantity_callback_query(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state = db.get_state(user_id)
    data = update.callback_query.data
    if data == 'back':
        state_list = state.split('_')
        category = state_list[1]
        item_id = int(state_list[2])
        item = db.get_items({'item': item_id})
        options = item['options']
        option_state = [list(d.keys())[0] for d in options]
        db.update_state(user_id, 'sell_%s_%d_%s_options' % (category, item_id, json.dumps(option_state)))
        msg = 'Selling a %s\n\nWhat %s is it?' % (item['itemName'].lower(), option_state[0].lower())
        keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
        keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
        keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def sell_quantity_message(bot, update):
    global db
    user_id = update.message.from_user.id
    try:
        quantity = int(update.message.text)
        state = db.get_state(user_id)
        state_list = state.split('_')
        item_id = int(state_list[2])
        options = state_list[3]
        item = db.get_items({'item': item_id})
        if quantity <= 0:
            msg = 'That\'s not a valid quantity. Please try again.'
            bot.send_message(user_id, msg)
        else:
            db.update_state(user_id, '_'.join(state_list[:-1]) + '_%d_price' % quantity)
            if options != 'null':
                price = float(item['items'][options]['price'])
            else:
                price = float(item['items']['price'])
            msg = 'You want to sell %s' % item['itemName']
            if options != 'null':
                msg += ': ' + ', '.join(json.loads(options))
            msg += '.\n\nPipsqueak store is currently selling the item for $%.2f. How much would you like to sell yours for? Please list the price per item.' % price
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid quantity. Please try again.'
        bot.send_message(user_id, msg)


def sell_price_callback_query(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state = db.get_state(user_id)
    data = update.callback_query.data
    if data == 'back':
        state_list = state.split('_')
        category = state_list[1]
        item_id = int(state_list[2])
        options = state_list[3]
        item = db.get_items({'item': item_id})
        db.update_state(user_id, 'sell_%s_%d_%s_quantity' % (category, item_id, options))
        msg = 'You want to sell %s' % item['itemName']
        if options != 'null':
            msg += ': ' + ', '.join(options)
        msg += '\n\nHow many do you want to sell?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def sell_price_message(bot, update):
    global db
    user_id = update.message.from_user.id
    try:
        price = round(float(update.message.text), 2)
        state = db.get_state(user_id)
        state_list = state.split('_')
        item_id = int(state_list[2])
        options = state_list[3]
        quantity = int(state_list[4])
        item = db.get_items({'item': item_id})
        if price <= 0:
            msg = 'That\'s not a valid amount. Please try again.'
            bot.send_message(user_id, msg)
        else:
            db.update_state(user_id, '_'.join(state_list[:-1]) + '_%.2f_confirm' % price)
            msg = 'You want to sell %s' % item['itemName']
            if options != 'null':
                msg += ': ' + ', '.join(json.loads(options))
            msg += '. Selling %d for $%.2f each.\n\nIs this correct?' % (quantity, price)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Confirm', callback_data='confirm')],
                                             [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid amount. Please try again.'
        bot.send_message(user_id, msg)


def sell_confirm(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state_list = state.split('_')
    category = state_list[1]
    item_id = int(state_list[2])
    options = state_list[3]
    quantity = int(state_list[4])
    price = round(float(state_list[5]), 2)
    data = update.callback_query.data
    if data == 'confirm':
        global admin_id
        db.update_state(user_id, 'home')
        item = db.get_items({'item': item_id})
        msg = 'Listing successful!\n\n%s' % item['itemName']
        if options != 'null':
            msg += ': ' + ', '.join(options)
        msg += '\nQuantity: %d\nPrice: $%.2f each\n\n' % (quantity, price)
        msg += 'We will contact you as soon as we have a buyer for your item. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        # TODO: Update database item listing
        msg = 'Listing: %s (%d) has listed the following item: %s (itemId: %d, quantity: %d, price: $%.2f)' % (update.callback_query.from_user.name, user_id, item['itemName'], item_id, quantity, price)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % update.callback_query.from_user.name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif data == 'back':
        item = db.get_items({'item': item_id})
        db.update_state(user_id, 'sell_%s_%d_%s_quantity' % (category, item_id, options))
        msg = 'You want to sell %s' % item['itemName']
        if options != 'null':
            msg += ': ' + ', '.join(options)
        msg += '\n\nHow many do you want to sell?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def sell_request(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'true':
        db.update_state(user_id, 'sell_request_item')
        msg = 'Alright, what item do you want to be sell?'
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=None)
    else:
        cancel(bot, update)


def sell_request_item(bot, update):
    global db
    global admin_id
    user_id = update.message.from_user.id
    name = update.message.from_user.name
    text = update.message.text
    db.add_request(user_id, name, text)
    db.update_state(user_id, 'home')
    msg = 'Got it! We will notify you as soon as possible after an admin reviewed your listing. Thank you for using Pipsqueak!'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
    bot.send_message(user_id, msg, reply_markup=keyboard)
    msg = 'Request: %s (%d) has requested to be notified for the following item: %s.' % (name, user_id, text)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Approve', callback_data='approve'), InlineKeyboardButton('Reject', callback_data='reject')],
                                     [InlineKeyboardButton('Contact %s' % name, callback_data='forward_%d' % user_id)]])
    bot.send_message(admin_id, msg, reply_markup=keyboard)


# Marketplace functions
def marketplace(bot, update):
    if pre_check(bot, update):
        global db
        msg = 'The marketplace is dedicated to student-listed items. Please note that we won\'t be issuing receipts for marketplace purchases.\n\nWhat category of items do you want to buy?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Materials', callback_data='Materials')],
                                         [InlineKeyboardButton('Electronics', callback_data='Electronics')],
                                         [InlineKeyboardButton('Adhesives', callback_data='Adhesives')],
                                         [InlineKeyboardButton('Stationery', callback_data='Stationery')],
                                         [InlineKeyboardButton('Amenities', callback_data='Amenities')],
                                         [InlineKeyboardButton('I can\'t find my item', callback_data='none')]])
        if update.callback_query is not None:
            user_id = update.callback_query.from_user.id
            msg_id = update.callback_query.message.message_id
            db.update_state(user_id, 'marketplace')
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            user_id = update.message.from_user.id
            db.update_state(user_id, 'marketplace')
            bot.send_message(user_id, msg, reply_markup=keyboard)


def marketplace_category(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data != 'none':
        items = db.get_items({'category': data, 'page': 0})
        if items:
            db.update_state(user_id, 'marketplace_%s_0_item' % data)
            msg = 'What %s do you want to buy?' % data.lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data='%s_%d' % (item['itemName'], int(item['itemId'])))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            query_id = update.callback_query.id
            msg = 'There are currently no listings of %s.' % data.lower()
            bot.answer_callback_query(query_id, msg)
    else:
        db.update_state(user_id, 'marketplace_request')
        msg = 'We\'re sorry you couldn\'t find what you want. You can check the official Pipsqueak store. Alternatively, would you like to be notified if your item becomes available?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                         [InlineKeyboardButton('Check Pipsqueak store', callback_data='buy')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def marketplace_item(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    print(data)
    if data == 'none':
        db.update_state(user_id, 'marketplace_request')
        msg = 'We\'re sorry you couldn\'t find what you want. You can check the official Pipsqueak store. Alternatively, would you like to be notified if your item becomes available?'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                         [InlineKeyboardButton('Check Pipsqueak store', callback_data='buy')],
                                         [InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'category':
        marketplace(bot, update)
    elif data == 'prev':
        state = db.get_state(user_id)
        state_list = state.split('_')
        page = int(state_list[2])
        if state_list[2] == 0:
            callback_query_id = update.callback_query.id
            msg = 'There is no previous page!'
            bot.answer_callback_query(callback_query_id, msg)
        else:
            db.update_state(user_id, 'marketplace_%s_%d_item' % (state_list[1], page - 1))
            items = db.get_items({'category': state_list[1], 'page': page - 1})
            msg = 'What %s do you want to buy?' % state_list[1].lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data='%s_%d' % (item['itemName'], int(item['itemId'])))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'next':
        state = db.get_state(user_id)
        state_list = state.split('_')
        page = int(state_list[2])
        items = db.get_items({'category': state_list[1], 'page': page + 1})
        if items:
            db.update_state(user_id, 'marketplace_%s_%d_item' % (state_list[1], page + 1))
            msg = 'What %s do you want to buy?' % state_list[1].lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data='%s_%d' % (item['itemName'], int(item['itemId'])))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            callback_query_id = update.callback_query.id
            msg = 'There is no next page!'
            bot.answer_callback_query(callback_query_id, msg)
    else:
        item_name = data.split('_')[0]
        item_id = int(data.split('_')[1])
        item_id = 5
        category = db.get_state(user_id).split('_')[1]
        print(category)
        item = db.get_listings({'item': item_id})
        print(item)
        if item:
            db.update_state(user_id, 'marketplace_%s_%d_seller' % (category, item_id))
            msg = 'We have these listings for %s:\n\n' % item_name
            keyboard = []
            for i in item:
                try:
                    properties = json.loads(i['properties'])
                except json.decoder.JSONDecodeError:
                    properties = i['properties']
                msg += 'ID%d: %s for $%.2f' % (int(i['listingId']), json.dumps(properties), float(i['price']))
                keyboard.append([InlineKeyboardButton('ID%d' % int(i['listingId']), callback_data=str(i['listingId']))])
            keyboard.append([InlineKeyboardButton('<< back', callback_data='back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            db.update_state(user_id, 'marketplace_%s_%d_nostock' % (category, item_id))
            msg = 'I\'m sorry, but we currently there are no listings for this item. You can check the official Pipsqueak store. Alternatively, would you like to be notified if your item becomes available?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                             [InlineKeyboardButton('Check Pipsqueak store', callback_data='buy')],
                                             [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


# def marketplace_options(bot, update, item_id, options_state):
#     global db
#     user_id = update.callback_query.from_user.id
#     msg_id = update.callback_query.message.message_id
#     data = update.callback_query.data
#     if data == '0_back':
#         category = db.get_state(user_id).split('_')[1]
#         items = json.loads(db.get_items_marketplace(category=category, page=0))
#         db.update_state(user_id, 'marketplace_%s_0_item' % category)
#         msg = 'What %s do you want to buy?' % category.lower()
#         keyboard = [[InlineKeyboardButton(item['itemName'], callback_data=str(item['itemId']))] for item in items]
#         keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'),
#                          InlineKeyboardButton('Next >>', callback_data='next')])
#         keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
#         keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
#         keyboard = InlineKeyboardMarkup(keyboard)
#         bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
#     elif data == 'back':
#         state = db.get_state(user_id)
#         item_id = int(state.split('_')[2])
#         item = json.loads(db.get_items_marketplace(item_id=item_id))
#         options = item['options']
#         option_state = [list(d.keys())[0] for d in options]
#         db.update_state(user_id, 'marketplace_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(option_state)))
#         msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
#         keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
#         keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
#         keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
#         keyboard = InlineKeyboardMarkup(keyboard)
#         bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
#     elif data == 'none':
#         db.update_state(user_id, 'marketplace_request')
#         msg = 'We\'re sorry you couldn\'t find what you want. You can check the official Pipsqueak store. Alternatively, would you like to be notified if your item becomes available?'
#         keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
#                                          [InlineKeyboardButton('Check Pipsqueak store', callback_data='buy')],
#                                          [InlineKeyboardButton('/cancel', callback_data='cancel')]])
#         bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
#     else:
#         data_l = data.split('_')
#         i = int(data_l[0])
#         option = data_l[1]
#         options_state[i] = option
#         if i < len(options_state) - 1:
#             item = json.loads(db.get_items_marketplace(item_id=item_id))
#             options = item['options']
#             d = options[i + 1]
#             k = list(d.keys())[0]
#             db.update_state(user_id, 'marketplace_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(options_state)))
#             msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), k.lower())
#             keyboard = [[InlineKeyboardButton(choice, callback_data='%d_%s' % (i + 1, choice))] for choice in d[k]]
#             keyboard.append([InlineKeyboardButton('<< back', callback_data='back')])
#             keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
#             keyboard = InlineKeyboardMarkup(keyboard)
#             bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
#         else:
#             item = json.loads(db.get_items_marketplace(item_id=item_id))
#             sellers = item['items'][options_state]
#             if len(sellers) > 0:
#                 db.update_state(user_id, 'marketplace_%s_%d_%s_seller' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(options_state)))
#                 msg = 'You want to buy %s: ' % item['itemName']
#                 msg += ', '.join(options_state)
#                 msg += '\n\nWe currently have these listings for this item.\n\n'
#                 keyboard = []
#                 for seller in sellers:  # TODO: Reformat based on database structure
#                     msg += '%d: %d in stock, $%.2f each\n' % (seller['sellerId'], seller['quantity'], seller['price'])
#                     keyboard.append([InlineKeyboardButton(str(seller['sellerId']), callback_data=str(seller['sellerId']))])
#                 msg += '\nWhich one would you like to buy?'
#                 keyboard.append([InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')])
#                 keyboard = InlineKeyboardMarkup(keyboard)
#                 bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
#             else:
#                 db.update_state(user_id, 'marketplace_%s_%d_nostock' % (db.get_state(user_id).split('_')[1], item_id))
#                 msg = 'I\'m sorry, but we currently there are no listings for this item. You can check the official Pipsqueak store. Alternatively, would you like to be notified if your item becomes available?'
#                 keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
#                                                  [InlineKeyboardButton('Check Pipsqueak store', callback_data='buy')],
#                                                  [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
#                 bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def marketplace_nostock(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state_list = state.split('_')
    item_id = int(state_list[2])
    data = update.callback_query.data
    if data == 'true':
        db.update_state(user_id, 'home')
        msg = 'Got it! We will notify you as soon as the item becomes available. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.send_message(user_id, msg, reply_markup=keyboard)
        name = update.callback_query.from_user.name
        item = json.loads(db.get_items({'item_id': item_id}))['itemName']
        msg = '%s (%d) has requested to be notified for the following item: %s.' % (name, user_id, item)
        bot.send_message(admin_id, msg)
    elif data == 'buy':
        item = db.get_items({'item': item_id})
        options = item['options']
        if options:
            option_state = [list(d.keys())[0] for d in options]
            db.update_state(user_id, 'buy_%s_%d_%s_options' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(option_state)))
            msg = 'Buying a %s\n\nWhat %s do you want?' % (item['itemName'].lower(), option_state[0].lower())
            keyboard = [[InlineKeyboardButton(option, callback_data='0_%s' % option)] for option in options[0][option_state[0]]]
            keyboard.append([InlineKeyboardButton('<< back', callback_data='0_back')])
            keyboard.append([InlineKeyboardButton('I can\'t find my item', callback_data='none')])
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            quantity = int(item['items']['quantity'])
            if quantity > 0:
                db.update_state(user_id, 'buy_%s_%d_null_quantity' % (db.get_state(user_id).split('_')[1], item_id))
                msg = 'You want to buy %s' % item['itemName']
                msg += '\n\nWe currently have %d in stock. How many do you want to buy?' % quantity
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
            else:
                db.update_state(user_id, 'buy_%s_%d_nostock' % (db.get_state(user_id).split('_')[1], item_id))
                msg = 'I\'m sorry, but we currently don\'t have that item in stock. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                                 [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                                 [InlineKeyboardButton('<< back', callback_data='back'),
                                                  InlineKeyboardButton('/cancel', callback_data='cancel')]])
                bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        category = state_list[1]
        items = db.get_items({'category': category, 'page': 0})
        if items:
            db.update_state(user_id, 'marketplace_%s_0_item' % data)
            msg = 'What %s do you want to buy?' % data.lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data='%s_%d' % (item['itemName'], int(item['itemId'])))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            query_id = update.callback_query.id
            msg = 'There are currently no listings of %s.' % category.lower()
            bot.answer_callback_query(query_id, msg)
    else:
        cancel(bot, update)


def marketplace_seller(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state_list = state.split('_')
    item_id = int(state_list[2])
    data = update.callback_query.data
    if data == 'back':
        category = state_list[1]
        items = db.get_items({'category': category, 'page': 0})
        if items:
            db.update_state(user_id, 'marketplace_%s_0_item' % data)
            msg = 'What %s do you want to buy?' % data.lower()
            keyboard = [[InlineKeyboardButton(item['itemName'], callback_data='%s_%d' % (item['itemName'], int(item['itemId'])))] for item in items]
            keyboard.append([InlineKeyboardButton('<< Prev', callback_data='prev'), InlineKeyboardButton('Next >>', callback_data='next')])
            keyboard.append([InlineKeyboardButton('Change category', callback_data='category')])
            keyboard.append(([InlineKeyboardButton('I can\'t find my item', callback_data='none')]))
            keyboard = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            query_id = update.callback_query.id
            msg = 'There are currently no listings of %s.' % category.lower()
            bot.answer_callback_query(query_id, msg)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        listing_id = int(data)
        seller_id = db.get_seller(listing_id)
        if seller_id == user_id:
            query_id = update.callback_query.id
            msg = 'You can\'t buy from yourself!'
            bot.answer_callback_query(query_id, msg)
        else:
            # TODO: Fix
            item = json.loads(db.get_listings({'item': item_id}))
            options_state = json.loads(state_list[3])
            quantity = item['items'][options_state][seller_id]['quantity']
            price = item['items'][options_state][seller_id]['price']
            db.update_state(user_id, '_'.join(state_list) + '_%d_quantity' % seller_id)
            msg = 'You want to buy %s: ' % item['itemName']
            msg += ', '.join(options_state)
            msg += 'from %d. There are currently %d in stock for $%.2f each. How many do you want to buy?' % (seller_id, quantity, price)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def marketplace_quantity_callback_query(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state = db.get_state(user_id)
    data = update.callback_query.data
    if data == 'back':
        state_list = state.split('_')
        category = state_list[1]
        item_id = int(state_list[2])
        options_state = json.loads(state_list[3])
        item = json.loads(db.get_listings({'item': item_id}))
        sellers = item['items'][options_state]
        db.update_state(user_id, 'marketplace_%s_%d_%s_seller' % (category, item_id, json.dumps(options_state)))
        msg = 'You want to buy %s: ' % item['itemName']
        msg += ', '.join(options_state)
        msg += '\n\nWe currently have these listings for this item.\n\n'
        keyboard = []
        for seller in sellers:  # TODO: Reformat based on database structure
            msg += '%d: %d in stock, $%.2f each\n' % (seller['sellerId'], seller['quantity'], seller['price'])
            keyboard.append([InlineKeyboardButton(str(seller['sellerId']), callback_data=str(seller['sellerId']))])
        msg += '\nWhich one would you like to buy?'
        keyboard.append([InlineKeyboardButton('<< back', callback_data='back'),
                         InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


def marketplace_quantity_message(bot, update):
    global db
    user_id = update.message.from_user.id
    try:
        quantity = int(update.message.text)
        state = db.get_state(user_id)
        state_list = state.split('_')
        item_id = int(state_list[2])
        options = json.loads(state_list[3])
        seller_id = int(state_list[4])
        item = json.loads(db.get_items_marketplace(item_id=item_id))
        stock = item['items'][options][seller_id]['quantity']
        if quantity <= 0:
            msg = 'That\'s not a valid quantity. Please try again.'
            bot.send_message(user_id, msg)
        elif quantity > stock:
            msg = 'That\'s more than the stock currently listed. Please try again.'
            bot.send_message(user_id, msg)
        else:
            db.update_state(user_id, '_'.join(state_list[-1]) + '_confirm')
            price = item['items'][options]['price']
            msg = 'You want to buy %s: ' % item['itemName']
            msg += ', '.join(options)
            msg += '. The item is currently listed for $%.2f each, $%.2f total for %d items.\n\n' % (price, quantity * price, quantity)
            msg += 'Please note that we won\'t be issuing receipts for marketplace purchases. Alternatively, you can check the official Pipsqueak store, where we will be issuing claimable receipts.\n\nWould you like to buy from the marketplace?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Buy from marketplace', callback_data='confirm')],
                                             [InlineKeyboardButton('Check Pipsqueak store', callback_data='buy')],
                                             [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid quantity. Please try again.'
        bot.send_message(user_id, msg)


def marketplace_confirm(bot, update, state):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    state_list = state.split('_')
    category = state_list[1]
    item_id = int(state_list[2])
    options = json.loads(state_list[3])
    seller_id = int(state_list[4])
    quantity = int(state_list[5])
    data = update.callback_query.data
    if data == 'confirm':
        global admin_id
        db.update_state(user_id, 'home')
        item = db.get_items_marketplace(item_id=item_id)
        msg = 'Purchase successful!\n\n%s: ' % item['itemName']
        msg += ', '.join(options)
        msg += 'Quantity: %d\nTotal price: $%.2f\n\n' % (quantity, quantity * item['items'][options][seller_id]['price'])
        msg += 'We will contact you soon for pickup details. Thank you for using Pipsqueak!'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        # TODO: Update database item quantity
        seller_name = db.get_name(seller_id)
        msg = 'Purchase: %s (%d) has purchased the following item: %s (itemId: %d) (quantity: %d) from %s (%d)' % (update.callback_query.from_user.name, user_id, item['itemName'], item_id, quantity, seller_name, seller_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % update.callback_query.from_user.name, callback_data='forward_%d' % user_id)],
                                         [InlineKeyboardButton('Contact %s' % seller_name, callback_data='forward_%d' % seller_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)
    elif data == 'buy':
        item = db.get_items({'item': item_id})
        quantity = item['items'][options]['quantity']
        if quantity > 0:
            db.update_state(user_id, 'buy_%s_%d_%s_quantity' % (db.get_state(user_id).split('_')[1], item_id, json.dumps(options)))
            msg = 'You want to buy %s: ' % item['itemName']
            msg += ', '.join(options)
            msg += '\n\nWe currently have %d in stock. How many do you want to buy?' % quantity
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'),
                                              InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        else:
            db.update_state(user_id, 'buy_%s_%d_nostock' % (db.get_state(user_id).split('_')[1], item_id))
            msg = 'I\'m sorry, but we currently don\'t have that item in stock. You can check the marketplace for student-listed items. Please note that we will not be issuing receipts for marketplace purchases. Alternatively, would you like to be notified if your item becomes available?'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Notify me', callback_data='true')],
                                             [InlineKeyboardButton('Check marketplace', callback_data='marketplace')],
                                             [InlineKeyboardButton('<< back', callback_data='back'),
                                              InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'back':
        item = db.get_items_marketplace(item_id=item_id)
        db.update_state(user_id, 'marketplace_%s_%d_%s_%d_quantity' % (category, item_id, json.dumps(options), quantity))
        price = item['items'][options][seller_id]['price']
        msg = 'You want to buy %s: ' % item['itemName']
        msg += ', '.join(options)
        msg += 'from %d. There are currently %d in stock for $%.2f each. How many do you want to buy?' % (seller_id, quantity, price)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    else:
        cancel(bot, update)


# Food functions
def food(bot, update):
    global db
    user_id = update.message.from_user.id
    state = db.get_state(user_id)
    if state == 'home':
        db.update_state(user_id, 'home_1')
        msg = 'Sorry, we are a parts marketplace. We\'re totally not selling food.'
        bot.send_message(user_id, msg)
    elif state == 'home_1':
        db.update_state(user_id, 'home_2')
        msg = 'Dude, seriously. We can\'t be selling food here. We are a PARTS marketplace.'
        bot.send_message(user_id, msg)
    elif state == 'home_2':
        db.update_state(user_id, 'food')
        msg = 'Sigh, fine... What do you want?'
        foods = db.get_food()
        keyboard = [[InlineKeyboardButton(item[1], callback_data=str(item[0]))] for item in foods]
        keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.send_message(user_id, msg, reply_markup=keyboard)
    else:
        msg = 'You\'re in the middle of an operation. Please finish what you\'re doing first or use /cancel.'
        bot.send_message(user_id, msg)


def food_item(bot, update):
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
        price = round(item[3], 2)
        db.update_state(user_id, 'food_%d_quantity' % item_id)
        msg = 'We have %s, %d in stock for $%.2f each. How many do you want to buy?' % (item_name, quantity, price)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def food_quantity_callback_query(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'cancel':
        cancel(bot, update)
    else:
        db.update_state(user_id, 'food')
        msg = 'What do you want?'
        foods = db.get_food()
        keyboard = [[InlineKeyboardButton(item[1], callback_data=str(item[0]))] for item in foods]
        keyboard.append([InlineKeyboardButton('/cancel', callback_data='cancel')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)


def food_quantity_message(bot, update):
    global db
    user_id = update.message.from_user.id
    state = db.get_state(user_id)
    state_list = state.split('_')
    item_id = int(state_list[1])
    item = db.get_food(item_id)
    print(item)
    item_name = item[1]
    stock = int(item[2])
    price = round(float(item[3]), 2)
    try:
        quantity = int(update.message.text)
        print(quantity)
        if quantity < 0:
            msg = 'That\'s not a valid quantity. Please try again.'
            bot.send_message(user_id, msg)
        elif quantity > stock:
            msg = 'That\'s more than we have in stock right now. Please try again.'
            bot.send_message(user_id, msg)
        else:
            print('hello')
            db.update_state(user_id, 'food_%d_%d_confirm' % (item_id, quantity))
            print('hi')
            msg = 'You\'re buying %s, %d for $%.2f each, total $%.2f. Is this correct?' % (item_name, quantity, price, quantity * price)
            print(msg)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Confirm', callback_data='confirm')],
                                             [InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
            bot.send_message(user_id, msg, reply_markup=keyboard)
    except ValueError:
        msg = 'That\'s not a valid quantity. Please try again.'
        bot.send_message(user_id, msg)


def food_confirm(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    msg_id = update.callback_query.message.message_id
    data = update.callback_query.data
    if data == 'back':
        state = db.get_state(user_id)
        state_list = state.split('_')
        item_id = int(state_list[1])
        item = db.get_food(item_id)
        item_name = item[1]
        quantity = item[2]
        price = round(item[3], 2)
        db.update_state(user_id, 'food_%d_quantity' % item_id)
        msg = 'We have %s, %d in stock for $%.2f each. How many do you want to buy?' % (item_name, quantity, price)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('<< back', callback_data='back'), InlineKeyboardButton('/cancel', callback_data='cancel')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
    elif data == 'cancel':
        cancel(bot, update)
    else:
        global admin_id
        state = db.get_state(user_id)
        state_list = state.split('_')
        item_id = int(state_list[1])
        quantity = int(state_list[2])
        db.bought_food(item_id, quantity)
        db.update_state(user_id, 'home')
        item = db.get_food(item_id)
        item_name = item[1]
        msg = 'Purchase successful: %s! We will contact you soon for pickup details. Thank you for using Pipsqueak!' % item_name
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Leave /feedback', callback_data='feedback')]])
        bot.edit_message_text(msg, user_id, msg_id, reply_markup=keyboard)
        name = update.callback_query.from_user.name
        msg = 'Purchase: %s (%d) purchased %s (quantity: %d)' % (name, user_id, item_name, quantity)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Contact %s' % name, callback_data='forward_%d' % user_id)]])
        bot.send_message(admin_id, msg, reply_markup=keyboard)


# Handlers
def message_handler(bot, update):
    user_id = update.message.from_user.id
    state = db.get_state(user_id)
    if state.startswith('buy'):
        if state.endswith('_quantity'):
            buy_quantity_message(bot, update)
        else:
            msg = 'I don\'t understand. Please follow the instructions above.'
            bot.send_message(user_id, msg)
    elif state.startswith('sell'):
        if state.endswith('_quantity'):
            sell_quantity_message(bot, update)
        elif state.endswith('_price'):
            sell_price_message(bot, update)
        elif state.endswith('_request_item'):
            sell_request_item(bot, update)
        else:
            msg = 'I don\'t understand. Please follow the instructions above.'
            bot.send_message(user_id, msg)
    elif state.startswith('marketplace'):
        if state.endswith('_quantity'):
            marketplace_quantity_message(bot, update)
        else:
            msg = 'I don\'t understand. Please follow the instructions above.'
            bot.send_message(user_id, msg)
    elif state.startswith('food'):
        if state.endswith('_quantity'):
            food_quantity_message(bot, update)
        else:
            msg = 'I don\'t understand. Please follow the instructions above.'
            bot.send_message(user_id, msg)
    elif state == 'request_item':
        request_item(bot, update)
    elif state == 'feedback':
        global admin_id
        db.add_feedback(user_id, update.message.from_user.name, ''.join(update.message.text.split(',')))
        msg_id = update.message.message_id
        bot.forward_message(admin_id, user_id, msg_id)
        msg = 'Got it! Anything else you want to feedback to us? Please use /done when you\'re finished!'
        bot.send_message(user_id, msg)
    elif state.startswith('forward'):
        target_id = int(state.split('_')[1])
        msg = update.message.text
        bot.send_message(target_id, msg)
    else:
        msg = 'Please use /start to begin trading!'
        bot.send_message(user_id, msg)
    print(state)


def callback_query_handler(bot, update):
    global db
    user_id = update.callback_query.from_user.id
    state = db.get_state(user_id)
    text = update.callback_query.message.text
    if text.startswith('Help: ') or text.startswith('Listing: ') or text.startswith('Purchase: '):
        connect(bot, update)
    elif text.startswith('Request: '):
        data = update.callback_query.data
        if data.startswith('forward_'):
            connect(bot, update)
        else:
            review_request(bot, update)
    elif text.startswith('An admin is connecting to you.'):
        msg_id = update.callback_query.message.message_id
        data = update.callback_query.data
        target_id = int(data.split('_')[1])
        db.update_state(user_id, data)
        msg = 'You are now connected to an admin. Please use /done when you\'re finished!'
        bot.edit_message_text(msg, user_id, msg_id)
        name = db.get_name(user_id)
        msg = 'You are now connected to %s. Please use /done when you\'re finished!' % name
        bot.send_message(target_id, msg)
    elif state.startswith('buy'):
        if state.endswith('_item'):
            buy_item(bot, update)
        elif state.endswith('_options'):
            state_list = state.split('_')
            item_id = int(state_list[2])
            options = json.loads(state_list[3])
            buy_options(bot, update, item_id, options)
        elif state.endswith('_quantity'):
            buy_quantity_callback_query(bot, update)
        elif state.endswith('_nostock'):
            buy_nostock(bot, update, state)
        elif state.endswith('_confirm'):
            buy_confirm(bot, update, state)
        elif state.endswith('_request'):
            request(bot, update)
        else:
            buy_category(bot, update)
    elif state.startswith('sell'):
        if state.endswith('_item'):
            sell_item(bot, update)
        elif state.endswith('_options'):
            state_list = state.split('_')
            item_id = int(state_list[2])
            options = json.loads(state_list[3])
            sell_options(bot, update, item_id, options)
        elif state.endswith('_quantity'):
            sell_quantity_callback_query(bot, update)
        elif state.endswith('_price'):
            sell_price_callback_query(bot, update)
        elif state.endswith('_confirm'):
            sell_confirm(bot, update, state)
        elif state.endswith('_request'):
            sell_request(bot, update)
        else:
            sell_category(bot, update)
    elif state.startswith('marketplace'):
        if state.endswith('_item'):
            marketplace_item(bot, update)
        # elif state.endswith('_options'):
        #     state_list = state.split('_')
        #     item_id = int(state_list[2])
        #     options = json.loads(state_list[3])
        #     marketplace_options(bot, update, item_id, options)
        elif state.endswith('_seller'):
            marketplace_seller(bot, update, state)
        elif state.endswith('_quantity'):
            marketplace_quantity_callback_query(bot, update)
        elif state.endswith('_nostock'):
            marketplace_nostock(bot, update, state)
        elif state.endswith('_confirm'):
            marketplace_confirm(bot, update, state)
        elif state.endswith('_request'):
            request(bot, update)
        else:
            marketplace_category(bot, update)
    elif state.startswith('food'):
        if state.endswith('_quantity'):
            food_quantity_callback_query(bot, update)
        elif state.endswith('_confirm'):
            food_confirm(bot, update)
        else:
            food_item(bot, update)
    elif state == 'home':
        if update.callback_query.data == 'buy':
            buy(bot, update)
        elif update.callback_query.data == 'sell':
            sell(bot, update)
        elif update.callback_query.data == 'feedback':
            feedback(bot, update)
        else:
            query_id = update.callback_query.id
            msg = 'Please use /start to begin trading!'
            bot.answer_callback_query(query_id, msg)
    else:
        query_id = update.callback_query.id
        msg = 'Please use /start to begin trading!'
        bot.answer_callback_query(query_id, msg)


def state_command(bot, update):
    global db
    user_id = update.message.from_user.id
    state = db.get_state(user_id)
    bot.send_message(user_id, state)


# Main
def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CommandHandler('done', done))
    dispatcher.add_handler(CommandHandler('feedback', feedback))
    dispatcher.add_handler(CommandHandler('buy', buy))
    dispatcher.add_handler(CommandHandler('sell', sell))
    dispatcher.add_handler(CommandHandler('marketplace', marketplace))
    dispatcher.add_handler(CommandHandler('request', request))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('food', food))
    dispatcher.add_handler(CommandHandler('_cancel', force_cancel))
    dispatcher.add_handler(CommandHandler('_state', state_command))

    dispatcher.add_handler(MessageHandler(filters.Filters.text, message_handler))

    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.setWebhook('https://pipsqueak-sutd-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    db = Database()
    admin_id = -258851839
    admins = (111914928, 230937024, 255484909, 42010966)
    main()

# TODO: Ask for email address to send receipt
