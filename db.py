import sqlite3

DB_NAME = "expenses.db"

def connect():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            amount REAL,
            category TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_expense(date, amount, category, description):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses (date, amount, category, description) VALUES (?, ?, ?, ?)",
                (date, amount, category, description))
    conn.commit()
    conn.close()

def get_expenses(year=None):
    conn = connect()
    cur = conn.cursor()
    if year and year != "All":
        cur.execute("SELECT id, date, amount, category, description FROM expenses WHERE substr(date,1,4)=? ORDER BY date DESC", (year,))
    else:
        cur.execute("SELECT id, date, amount, category, description FROM expenses ORDER BY date DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_years():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT substr(date,1,4) FROM expenses ORDER BY substr(date,1,4) ASC")
    years = [y[0] for y in cur.fetchall() if y[0]]
    conn.close()
    return years

def delete_expense_by_id(expense_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()

def get_monthly_summary(year):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT substr(date,6,2) AS month, SUM(amount) FROM expenses WHERE substr(date,1,4)=? GROUP BY month",
        (year,))
    rows = cur.fetchall()
    conn.close()
    return rows
