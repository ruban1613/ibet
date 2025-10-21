import os, sys, django
sys.path.insert(0, os.path.join('.', 'IBET'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()
from django.db import connection
cursor = connection.cursor()

cursor.execute('SELECT id, balance FROM dailywage_module_dailywagewallet;')
rows = cursor.fetchall()
print('ID | Balance')
print('-' * 20)
for row in rows:
    print(f'{row[0]} | {row[1]}')
