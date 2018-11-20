import os
import psycopg2
import pytz
from datetime import datetime
import json
import requests
from urllib.parse import urlencode


def get_date():
    return str(datetime.now(pytz.timezone('Asia/Singapore')).date())


def get_time():
    return str(datetime.now(pytz.timezone('Asia/Singapore')).time())[:8]


def print_json(d):
    if d:
        s = json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))
        print(s)


class Database(object):

    def __init__(self):
        self.url = 'http://phpstack-212261-643485.cloudwaysapps.com'
        os.environ['DATABASE_URL'] = 'postgres://oylxidwhboayxg:abdc45f4642fa9f329bef28f8e31f967c91d64c1dae3eab5d30e7b6fb62096be@ec2-174-129-32-37.compute-1.amazonaws.com:5432/d52lcq3tkapjck'
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cur = self.conn.cursor()
        stmt = "CREATE TABLE IF NOT EXISTS user_database (user_id BIGINT NOT NULL, name TEXT NOT NULL, state TEXT NOT NULL)"
        self.commit(stmt)
        stmt = "CREATE TABLE IF NOT EXISTS requests (date TEXT, time TEXT, user_id BIGINT NOT NULL, name TEXT NOT NULL, item TEXT NOT NULL)"
        self.commit(stmt)
        stmt = "CREATE TABLE IF NOT EXISTS feedback (date TEXT NOT NULL, time TEXT NOT NULL, user_id BIGINT NOT NULL, name TEXT NOT NULL, feedback TEXT NOT NULL)"
        self.commit(stmt)
        stmt = "CREATE TABLE IF NOT EXISTS food (item_id BIGINT NOT NULL, item_name TEXT NOT NULL, quantity BIGINT NOT NULL, price REAL NOT NULL)"
        self.commit(stmt)
        stmt = "CREATE TABLE IF NOT EXISTS activities (date TEXT NOT NULL, time TEXT NOT NULL, user_id BIGINT NOT NULL, user_name TEXT NOT NULL, state TEXT NOT NULL, activity TEXT NOT NULL)"
        self.commit(stmt)

    def commit(self, stmt):
        self.cur.execute(stmt)
        self.conn.commit()

    def fetch(self, stmt):
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def drop_table(self, table_name):
        stmt = "DROP TABLE %s" % table_name
        self.commit(stmt)

    # User functions
    def add_new_user(self, user_id, user_name):
        state = {'state': 'home', 'substate': 'home', 'item_state': None}
        state_json = json.dumps(state)
        stmt = "INSERT INTO user_database VALUES (%d, '%s', '%s')" % (user_id, user_name, state_json)
        self.commit(stmt)

    def get_users(self, admin=False):
        if admin:
            stmt = "SELECT * FROM user_database"
            rows = self.fetch(stmt)
            return rows
        else:
            stmt = "SELECT user_id FROM user_database"
            rows = self.fetch(stmt)
            return [x[0] for x in rows]

    def get_name(self, user_id):
        stmt = "SELECT name FROM user_database WHERE user_id = %d" % user_id
        rows = self.fetch(stmt)
        if rows[0]:
            return rows[0][0]
        else:
            return ''

    def get_state(self, user_id):
        stmt = "SELECT state FROM user_database WHERE user_id = %d" % user_id
        rows = self.fetch(stmt)
        state = json.loads(rows[0][0])
        return state

    def update_state(self, user_id, state):
        state_json = json.dumps(state)
        stmt = "UPDATE user_database SET state = '%s' WHERE user_id = %d" % (state_json, user_id)
        self.commit(stmt)

    # Inventory functions
    def get_items(self, category, page):
        url = self.url + '/ajax/items?category=%s&page=%d' % (category, page)
        r = requests.get(url)
        try:
            r = json.loads(r.text)
            return r
        except json.decoder.JSONDecodeError:
            return []

    def get_item_details(self, item_id):
        url = self.url + '/ajax/items?item=%d' % item_id
        r = requests.get(url)
        try:
            r = json.loads(r.text)
            return r
        except json.decoder.JSONDecodeError:
            return {}

    def bought_item(self, args):
        url = self.url + '/ajax/b-cbuy?' + urlencode(args)
        r = requests.get(url)
        return r.text

    # Listings function
    def get_listings(self, item_id):
        url = self.url + '/ajax/getlistings?item=%d' % item_id
        r = requests.get(url)
        try:
            r = json.loads(r.text)
            return r
        except json.decoder.JSONDecodeError:
            return []

    def get_listing_details(self, listing_id):
        url = self.url + '/ajax/getlistings?listingid=%d' % listing_id
        r = requests.get(url)
        try:
            r = json.loads(r.text)
            return r
        except json.decoder.JSONDecodeError:
            return {}

    def bought_listing(self, args):
        url = self.url + '/ajax/c-cbuy?' + urlencode(args)
        r = requests.get(url)
        return r.text

    # Food functions
    def get_foods(self):
        stmt = "SELECT * FROM food WHERE quantity > 0 ORDER BY item_id"
        rows = self.fetch(stmt)
        return rows

    def get_food_details(self, item_id):
        stmt = "SELECT * FROM food WHERE item_id = %d" % item_id
        rows = self.fetch(stmt)
        return rows[0]

    def bought_food(self, item_id, quantity):
        food = self.get_food_details(item_id)
        q = food[2]
        stmt = "UPDATE food SET quantity = %d WHERE item_id = %d" % (q - quantity, item_id)
        self.commit(stmt)

    # Other functions
    def get_requests(self):
        stmt = "SELECT * FROM requests ORDER BY date, time"
        rows = self.fetch(stmt)
        return rows

    def add_requests(self, user_id, name, item):
        date = get_date()
        time = get_time()
        item = ''.join(item.split("'"))
        stmt = "INSERT INTO requests VALUES ('%s', '%s', %d, '%s', '%s')" % (date, time, user_id, name, item)
        self.commit(stmt)

    def delete_request(self, item):
        stmt = "DELETE FROM requests WHERE item = '%s'" % item
        self.commit(stmt)

    def get_feedback(self):
        stmt = "SELECT * FROM feedback ORDER BY date, time"
        rows = self.fetch(stmt)
        return rows

    def add_feedback(self, user_id, name, feedback):
        date = get_date()
        time = get_time()
        feedback = ''.join(feedback.split("'"))
        stmt = "INSERT INTO feedback VALUES ('%s', '%s', %d, '%s', '%s')" % (date, time, user_id, name, feedback)
        self.commit(stmt)

    def get_activities(self):
        stmt = "SELECT * FROM activities ORDER BY date, time"
        rows = self.fetch(stmt)
        return rows

    def add_activity(self, user_id, name, state, activity):
        date = get_date()
        time = get_time()
        state = json.dumps(state)
        activity = ''.join(activity.split("'"))
        stmt = "SELECT * FROM activities WHERE date = '%s' AND time = '%s' AND user_id = %d" % (date, time, user_id)
        rows = self.fetch(stmt)
        if not rows:
            stmt = "INSERT INTO activities VALUES ('%s', '%s', %d, '%s', '%s', '%s')" % (date, time, user_id, name, state, activity)
            self.commit(stmt)