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
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS c2c_inventory (date TEXT NOT NULL, item_id TEXT NOT NULL, category TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, quantity INT NOT NULL, price REAL NOT NULL, seller_id BIGINT NOT NULL, status TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS requests (user_id BIGINT NOT NULL, name TEXT NOT NULL, item TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS feedback (date TEXT NOT NULL, time TEXT NOT NULL, user_id BIGINT NOT NULL, name TEXT NOT NULL, feedback TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS mascot_names (date TEXT NOT NULL, time TEXT NOT NULL, user_id BIGINT NOT NULL, user_name TEXT NOT NULL, submission TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS food (item_id BIGINT NOT NULL, item_name TEXT NOT NULL, quantity BIGINT NOT NULL, price REAL NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()

    def get_items(self, args=None):
        url = self.url + '/ajax/items'
        if args:
            url += '?' + urlencode(args)
        r = requests.get(url)
        try:
            r = json.loads(r.text)
            return r
        except json.decoder.JSONDecodeError:
            return []

    def bought_item(self, args):
        url = self.url + '/ajax/b-cbuy?' + urlencode(args)
        r = requests.get(url)
        return r.text

    def get_listings(self, args):
        url = self.url + '/ajax/getlistings?'
        url += urlencode(args)
        r = requests.get(url)
        try:
            r = json.loads(r.text)
            return r
        except json.decoder.JSONDecodeError:
            return []

    def get_seller(self, listing_id):
        # TODO: Fill in
        return 111914928

    def bought_listing(self, args):
        url = self.url + '/ajax/c-cbuy?' + urlencode(args)
        r = requests.get(url)
        return r.text

    def add_mascot_name(self, user_id, user_name, submission):
        date = get_date()
        time = get_time()
        stmt = "INSERT INTO mascot_names VALUES ('%s', '%s', %d, '%s', '%s')" % (date, time, user_id, user_name, submission)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_mascot_names(self):
        stmt = "SELECT * FROM mascot_names ORDER BY date, time"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def drop_table(self, table_name):
        stmt = "DROP TABLE %s" % table_name
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_user(self, user_id, name, state='home'):
        stmt = "INSERT INTO user_database (user_id, name, state) VALUES (%d, '%s', '%s')" % (user_id, name, state)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_users(self, admin=False):
        if admin:
            stmt = "SELECT * FROM user_database"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows
        else:
            stmt = "SELECT user_id FROM user_database"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return [x[0] for x in rows]

    def get_name(self, user_id):
        stmt = "SELECT name FROM user_database WHERE user_id = %d" % user_id
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        if rows:
            return rows[0][0]
        else:
            return ''

    def get_state(self, user_id):
        stmt = "SELECT state FROM user_database WHERE user_id = %d" % user_id
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows[0][0]

    def update_state(self, user_id, new_state):
        stmt = "UPDATE user_database SET state = '%s' WHERE user_id = %d" % (new_state, user_id)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_items_list(self, in_transaction=False):
        if not in_transaction:
            stmt = "SELECT date, item_id, category, name, description, quantity, price FROM c2c_inventory WHERE status = 'Ready' ORDER BY item_id"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows
        else:
            stmt = "SELECT item_id, name, description FROM c2c_inventory WHERE status != 'Ready' AND status != 'Pending' ORDER BY item_id"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows

    def get_items_dict(self, item_id=None, seller_id=None, category=None):
        if item_id:
            stmt = "SELECT * FROM c2c_inventory WHERE item_id = '%s'" % item_id
            self.cur.execute(stmt)
            item = self.cur.fetchall()[0]
            if item:
                item_d = {'date': item[0],
                          'item_id': item[1],
                          'category': item[2],
                          'name': item[3],
                          'description': item[4],
                          'quantity': item[5],
                          'price': round(float(item[6]), 2),
                          'seller_id': item[7],
                          'status': item[8]}
            else:
                item_d = {}
            return item_d
        elif seller_id:
            stmt = "SELECT date, item_id, category, name, description, price, status FROM c2c_inventory WHERE seller_id = '%s' AND (status = 'Ready' OR status = 'Pending') ORDER BY item_id" % seller_id
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            if rows:
                items = [{'date': item[0],
                          'item_id': item[1],
                          'category': item[2],
                          'name': item[3],
                          'description': item[4],
                          'price': round(float(item[5]), 2),
                          'status': item[6]} for item in rows]
            else:
                items = []
            return items
        elif category:
            stmt = "SELECT date, item_id, category, name, description, quantity, price FROM c2c_inventory WHERE category = '%s' AND status = 'Ready' ORDER BY item_id" % category
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            if rows:
                items = [{'date': item[0],
                          'item_id': item[1],
                          'category': item[2],
                          'name': item[3],
                          'description': item[4],
                          'quantity': item[5],
                          'price': round(float(item[6]), 2)} for item in rows]
            else:
                items = []
            return items
        else:
            stmt = "SELECT date, item_id, category, name, description, price FROM c2c_inventory WHERE status = 'Ready' ORDER BY item_id"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            items = [{'date': item[0],
                      'item_id': item[1],
                      'category': item[2],
                      'name': item[3],
                      'description': item[4],
                      'price': round(float(item[5]), 2)} for item in rows]
            return items

    def _get_items_admin(self):
        stmt = "SELECT * FROM c2c_inventory ORDER BY item_id"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def delete_item(self, item_id):
        stmt = "DELETE FROM c2c_inventory WHERE item_id = '%s'" % item_id
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_item(self, category, seller_id):
        stmt = "SELECT item_id FROM c2c_inventory WHERE category = '%s'" % category
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        if rows:
            item_id = '%s%04d' % (category[0], max([int(item[0][1:]) for item in rows]) + 1)
        else:
            item_id = '%s0001' % category[0]
        date = get_date()
        stmt = "INSERT INTO c2c_inventory VALUES ('%s', '%s', '%s', 'name', 'description', 0.0, %d, 'Pending', 1)" % (date, item_id, category, seller_id)
        self.cur.execute(stmt)
        self.conn.commit()
        return item_id

    def get_quantity(self, item_id):
        stmt = "SELECT quantity FROM c2c_inventory WHERE item_id = '%s'" % item_id
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        if rows[0]:
            return rows[0][0]
        else:
            return 0

    def update_item(self, item_id, column, value):
        if column == 'price':
            try:
                stmt = "UPDATE c2c_inventory SET price = %.2f WHERE item_id = '%s'" % (float(value), item_id)
            except ValueError:
                try:
                    stmt = "UPDATE c2c_inventory SET price = %.2f WHERE item_id = '%s'" % (float(value[1:]), item_id)
                except ValueError:
                    return False
        elif column == 'seller_id':
            stmt = "UPDATE c2c_inventory SET seller_id = %d WHERE item_id = '%s'" % (value, item_id)
        elif column == 'quantity':
            try:
                stmt = "UPDATE c2c_inventory SET quantity = %d WHERE item_id = '%s'" % (int(value), item_id)
                if int(value) <= 0:
                    return False
            except ValueError:
                return False
        else:
            if "'" in value:
                value = ''.join(value.split("'"))
            stmt = "UPDATE c2c_inventory SET %s = '%s' WHERE item_id = '%s'" % (column, value, item_id)
        self.cur.execute(stmt)
        self.conn.commit()
        return True

    def add_request(self, user_id, name, item):
        if "'" in item:
            item = ''.join(item.split("'"))
        stmt = "INSERT INTO requests VALUES (%d, '%s', '%s')" % (user_id, name, item)
        self.cur.execute(stmt)
        self.conn.commit()

    def delete_request(self, user_id, item):
        stmt = "DELETE FROM requests WHERE user_id = %d AND item = '%s'" % (user_id, item)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_requests(self):
        stmt = "SELECT * FROM requests"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def add_feedback(self, user_id, name, feedback):
        date = get_date()
        time = get_time()
        if "'" in feedback:
            feedback = ''.join(feedback.split("'"))
        stmt = "INSERT INTO feedback VALUES ('%s', '%s', %d, '%s', '%s')" % (date, time, user_id, name, feedback)
        self.cur.execute(stmt)
        self.conn.commit()

    def clear_table(self, table_name):
        stmt = "DELETE FROM %s" % table_name
        self.cur.execute(stmt)
        self.conn.commit()

    def get_feedback(self):
        stmt = "SELECT * FROM feedback ORDER BY date, time"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def get_food(self, item_id=None):
        if item_id:
            stmt = "SELECT * FROM food WHERE item_id = %d" % item_id
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows[0]
        else:
            stmt = "SELECT * FROM food WHERE quantity > 0 ORDER BY item_id"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows

    def bought_food(self, item_id, quantity):
        food = self.get_food(item_id)
        q = food[2]
        stmt = "UPDATE food SET quantity = %d WHERE item_id = %d" % (q - quantity, item_id)
        self.cur.execute(stmt)
        self.conn.commit()


if __name__ == '__main__':
    db = Database()
    # db.update_state(111914928, 'home')
    users = db.get_users(True)
    for user in users:
        print(user)
    items = db._get_items_admin()
    for item in items:
        print(item)
    items = db.get_mascot_names()
    for item in items:
        print(item)
    items = db.get_requests()
    for item in items:
        print(item)
    items = db.get_food()
    for item in items:
        print(item)
    print(len(users))
