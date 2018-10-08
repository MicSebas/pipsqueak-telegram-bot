import os
import psycopg2
import pytz
from datetime import datetime


def get_date():
    return str(datetime.now(pytz.timezone('Asia/Singapore')).date())


class Database(object):

    def __init__(self):
        os.environ['DATABASE_URL'] = 'postgres://oylxidwhboayxg:abdc45f4642fa9f329bef28f8e31f967c91d64c1dae3eab5d30e7b6fb62096be@ec2-174-129-32-37.compute-1.amazonaws.com:5432/d52lcq3tkapjck'
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cur = self.conn.cursor()
        stmt = "CREATE TABLE IF NOT EXISTS user_database (user_id BIGINT NOT NULL, name TEXT NOT NULL, state TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS catalog (date TEXT NOT NULL, item_id TEXT NOT NULL, category TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, price REAL NOT NULL, seller_id BIGINT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()

    def drop_table(self, table_name):
        stmt = "DROP TABLE %s" % table_name
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_user(self, user_id, name, state='home'):
        stmt = "INSERT INTO user_database (user_id, name, state) VALUES (%d, '%s', '%s')" % (user_id, name, state)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_users(self, with_name=False):
        if with_name:
            stmt = "SELECT user_id, name FROM user_database"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows
        else:
            stmt = "SELECT user_id FROM user_database"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return [x[0] for x in rows]

    def get_state(self, user_id):
        stmt = "SELECT state FROM user_database WHERE user_id = %d" % user_id
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows[0][0]

    def update_state(self, user_id, new_state):
        stmt = "UPDATE user_database SET state = '%s' WHERE user_id = %d" % (new_state, user_id)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_items_list(self):
        stmt = "SELECT date, item_id, category, name, description, price FROM catalog ORDER BY item_id"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def get_items_dict(self, item_id=None, seller_id=None, category=None):
        if item_id:
            stmt = "SELECT date, item_id, category, name, description, price FROM catalog WHERE item_id = '%s'" % item_id
            self.cur.execute(stmt)
            item = self.cur.fetchall()[0]
            item_d = {'date': item[0],
                      'item_id': item[1],
                      'category': item[2],
                      'name': item[3],
                      'description': item[4],
                      'price': round(float(item[5]), 2)}
            return item_d
        elif seller_id:
            stmt = "SELECT date, item_id, category, name, description, price FROM catalog WHERE seller_id = '%s'" % seller_id
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            items = [{'date': item[0],
                      'item_id': item[1],
                      'category': item[2],
                      'name': item[3],
                      'description': item[4],
                      'price': round(float(item[5]), 2)} for item in rows]
            return items
        elif category:
            stmt = "SELECT date, item_id, category, name, description, price FROM catalog WHERE category = '%s'" % category
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            items = [{'date': item[0],
                      'item_id': item[1],
                      'category': item[2],
                      'name': item[3],
                      'description': item[4],
                      'price': round(float(item[5]), 2)} for item in rows]
            return items
        else:
            stmt = "SELECT date, item_id, category, name, description, price FROM catalog"
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
        stmt = "SELECT * FROM catalog ORDER BY item_id"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def delete_item(self, item_id):
        stmt = "DELETE FROM catalog WHERE item_id = '%s'" % item_id
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_item(self, category, seller_id):
        stmt = "SELECT item_id FROM catalog WHERE category = '%s' ORDER BY item_id"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        if rows:
            item_id = '%s%04d' % (category[0], int(rows[-1][0][1:]) + 1)
        else:
            item_id = '%s0001' % category[0]
        date = get_date()
        stmt = "INSERT INTO catalog VALUES ('%s', '%s', '%s', 'name', 'description', 0.0, %d)" % (date, item_id, category, seller_id)
        self.cur.execute(stmt)
        self.conn.commit()
        return item_id

    def update_item(self, item_id, column, value):
        if column == 'price':
            try:
                stmt = "UPDATE catalog SET price = %.2f WHERE item_id = '%s'" % (float(value), item_id)
            except ValueError:
                stmt = "UPDATE catalog SET price = %.2f WHERE item_id = '%s'" % (float(value[1:]), item_id)
        else:
            stmt = "UPDATE catalog SET %s = '%s' WHERE item_id = '%s'" % (column, value, item_id)
        self.cur.execute(stmt)
        self.conn.commit()


if __name__ == '__main__':
    db = Database()
    print(db.get_users())
    # items = db.get_items()
    # for item in items:
    #     print(item)
