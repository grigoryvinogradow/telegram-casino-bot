
class UserError(Exception):
    pass

class UserNotFound(Exception):
    pass

class Users:
    def __init__(self, database):
        self.database = database
        self.cur = self.database.db

        self.cur.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT, congratulate BOOL
            );

            CREATE TABLE IF NOT EXISTS tries (
                id INTEGER PRIMARY KEY,
                slots INTEGER, dice INTEGER, dart INTEGER,
                bask INTEGER, foot INTEGER, bowl INTEGER
            );

            CREATE TABLE IF NOT EXISTS wins (
                id INTEGER PRIMARY KEY,
                slots INTEGER, dice INTEGER, dart INTEGER,
                bask INTEGER, foot INTEGER, bowl INTEGER
            );

            CREATE TABLE IF NOT EXISTS jackpots (
                id INTEGER PRIMARY KEY,
                slots INTEGER
            );
        ''')

    def add(self, id: int, name: str):
        try:
            self.cur.execute("BEGIN")
            self.cur.execute("INSERT INTO users (id, name, congratulate) VALUES (?, ?, ?)", (id, name, True)) # The main table
            self.cur.execute("INSERT INTO tries (id, slots, dice, dart, bask, foot, bowl) VALUES (?, ?, ?, ?, ?, ?, ?)", (id, 0, 0, 0, 0, 0, 0)) # Table with user's tries
            self.cur.execute("INSERT INTO wins (id, slots, dice, dart, bask, foot, bowl) VALUES (?, ?, ?, ?, ?, ?, ?)", (id, 0, 0, 0, 0, 0, 0)) # Table with user's wins
            self.cur.execute("INSERT INTO jackpots (id, slots) VALUES (?, ?)", (id, 0)) # Table with user's jackpots
            self.cur.execute("COMMIT")
        except Exception as e: raise UserError(e)

    def reset(self, id: int):
        try:
            self.cur.execute("BEGIN")
            self.cur.execute("UPDATE tries SET slots=0, dice=0, dart=0, bask=0, foot=0, bowl=0 WHERE id=?", (id,))
            self.cur.execute("UPDATE wins SET slots=0, dice=0, dart=0, bask=0, foot=0, bowl=0 WHERE id=?", (id,))
            self.cur.execute("UPDATE jackpots SET slots=0 WHERE id=?", (id,))
            self.cur.execute("COMMIT")
        except Exception as e: raise UserError(e)

    def get(self, table: str, id: int):
        try:            
            self.cur.execute(f"SELECT * FROM {table} WHERE id = ?", (id,))
            columns = [description[0] for description in self.cur.description]
            return next((dict(zip(columns, row)) for row in self.cur.fetchall()), None)
        except Exception as e: raise UserError(e)
    
    def set(self, table: str, id: int, parameter: str, value):
        try:
            self.cur.execute(
                f"UPDATE {table} SET {parameter} = ? WHERE id = ?",
                (value, id,)
            )
            self.database.conn.commit()
        except Exception as e: raise UserError(e)

    def increment(self, table: str, id: int, parameter: str):
        try:
            self.cur.execute(
                f"UPDATE {table} SET {parameter} = {parameter} + 1 WHERE id = ?",
                (id,)
            )
            self.database.conn.commit()
        except Exception as e: raise UserError(e)

    def get_all(self, table: str) -> list:
        self.cur.execute(f"SELECT * FROM {table}")
        columns = [description[0] for description in self.cur.description]
        return [dict(zip(columns, row)) for row in self.cur.fetchall()]