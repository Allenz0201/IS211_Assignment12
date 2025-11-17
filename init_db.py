import sqlite3

def init_db():
    conn = sqlite3.connect("hw13.db")
    with open("schema.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.commit()
    conn.close()
    print("Database hw13.db created and initialized.")

if __name__ == "__main__":
    init_db()
