import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT id, balance FROM dailywage_module_dailywagewallet')
rows = cursor.fetchall()
print('Daily wage wallet balances:')
for row in rows:
    print(f'ID: {row[0]}, Balance: {row[1]}')
conn.close()
