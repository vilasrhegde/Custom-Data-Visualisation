# db_setup.py
import sqlite3

def create_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS datasets
                 (id INTEGER PRIMARY KEY, name TEXT, description TEXT, data BLOB)''')
    conn.commit()
    conn.close()



if __name__ == '__main__':
    create_db()
