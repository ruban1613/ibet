import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check all wallet tables for corrupted balances
tables = [
    'dailywage_module_dailywagewallet',
    'individual_module_individualwallet',
    'couple_module_couplewallet',
    'retiree_module_retireewallet'
]

for table in tables:
    try:
        cursor.execute(f'SELECT id, balance FROM {table}')
        rows = cursor.fetchall()
        print(f'\n{table}:')
        for row in rows:
            balance = row[1]
            if balance is not None:
                try:
                    # Try to convert to float to check if it's valid
                    float(balance)
                    print(f'  ID: {row[0]}, Balance: {balance}')
                except (ValueError, TypeError):
                    print(f'  ID: {row[0]}, Balance: {repr(balance)} (CORRUPTED)')
            else:
                print(f'  ID: {row[0]}, Balance: None')
    except sqlite3.OperationalError as e:
        print(f'Error querying {table}: {e}')

conn.close()
