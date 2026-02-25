import sqlite3
from datetime import date
import random

DB = "demo.db"

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS accounts")
    cur.execute("DROP TABLE IF EXISTS subscriptions")
    cur.execute("DROP TABLE IF EXISTS invoices")

    cur.execute("CREATE TABLE accounts(id INTEGER PRIMARY KEY, name TEXT)")
    cur.execute("CREATE TABLE subscriptions(id INTEGER PRIMARY KEY, account_id INTEGER, mrr REAL, start_date TEXT, end_date TEXT)")
    cur.execute("CREATE TABLE invoices(id INTEGER PRIMARY KEY, account_id INTEGER, amount REAL, currency TEXT, invoice_date TEXT)")

    for i in range(1, 11):
        cur.execute("INSERT INTO accounts(id, name) VALUES(?, ?)", (i, f'Account_{i}'))

    sid = 1
    iid = 1
    for acc in range(1, 11):
        mrr = random.choice([100, 250, 500, 1200])
        cur.execute("INSERT INTO subscriptions VALUES(?, ?, ?, ?, ?)", (sid, acc, mrr, "2024-01-01", None))
        sid += 1
        for month in range(1, 13):
            amount = mrr + random.choice([0, 50, -20])
            cur.execute("INSERT INTO invoices VALUES(?, ?, ?, ?, ?)", (iid, acc, amount, "CAD", f"2025-{month:02d}-15"))
            iid += 1

    conn.commit()
    conn.close()
    print("Seeded demo.db")

if __name__ == "__main__":
    main()
