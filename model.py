class Database:
    def __init__(self, name):
        import sqlite3
        self.con = sqlite3.connect(name, check_same_thread=False)
        self.cur = self.con.cursor()

    def find_all(self, type):
        result = self.cur.execute(f"SELECT * FROM {type}").fetchall()
        return result

