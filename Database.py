import os
import psycopg2


class Database(object):

    def __init__(self):
        os.environ['DATABASE_URL'] = 'postgres://oylxidwhboayxg:abdc45f4642fa9f329bef28f8e31f967c91d64c1dae3eab5d30e7b6fb62096be@ec2-174-129-32-37.compute-1.amazonaws.com:5432/d52lcq3tkapjck'
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cur = self.conn.cursor()
        stmt = "CREATE TABLE IF NOT EXISTS user_database (user_id BIGINT NOT NULL, name TEXT NOT NULL, state TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS logs (item_id TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, condition TEXT NOT NULL, price REAL NOT NULL, seller_id BIGINT NOT NULL, seller_name TEXT NOT NULL)"
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_user(self, user_id, name):
        stmt = "INSERT INTO user_database (user_id, name, state) VALUES (%d, '%s', 'home')" % (user_id, name)
        self.cur.execute(stmt)
        self.conn.commit()

    def get_users(self):
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

    def drop_table(self, table_name):
        stmt = "DROP TABLE %s" % table_name
        self.cur.execute(stmt)
        self.conn.commit()

    def get_items(self, item_id=None, user_id=None):
        if item_id:
            stmt = "SELECT item_id, name, description, condition, price FROM logs WHERE item_id = '%s'" % item_id
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows[0]
        elif user_id:
            stmt = "SELECT item_id, name FROM logs WHERE user_id = %d" % user_id
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows[0]
        else:
            stmt = "SELECT item_id, name, description, condition, price FROM logs ORDER BY item_id"
            self.cur.execute(stmt)
            rows = self.cur.fetchall()
            return rows

    def admin_get_items(self):
        stmt = "SELECT * FROM logs ORDER BY item_id"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        return rows

    def delete_item(self, item_id):
        stmt = "DELETE FROM logs WHERE item_id = '%s'" % item_id
        self.cur.execute(stmt)
        self.conn.commit()

    def add_new_item(self, category, user_id, user_name):
        stmt = "SELECT item_id FROM logs ORDER BY item_id"
        self.cur.execute(stmt)
        rows = self.cur.fetchall()
        if rows:
            new_item_code = '%s%04d' % (category, max([int(i[0][1:]) for i in rows])+1)
        else:
            new_item_code = '%s0001' % category
        stmt = "INSERT INTO logs VALUES ('%s', 'name', 'description', 'condition', 0, %d, '%s')" % (new_item_code, user_id, user_name)
        self.cur.execute(stmt)
        self.conn.commit()
        return new_item_code

    def update_item(self, item_id, column, value):
        if column == 'price':
            stmt = "UPDATE logs SET %s = %.2f WHERE item_id = '%s'" % (column, float(value), item_id)
        else:
            stmt = "UPDATE logs SET %s = '%s' WHERE item_id = '%s'" % (column, value, item_id)
        self.cur.execute(stmt)
        self.conn.commit()


if __name__ == '__main__':
    db = Database()
    print(db.get_state(111914928))
    rows = db.get_items()
    for item in rows:
        print(item)
