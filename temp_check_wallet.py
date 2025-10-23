import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from student_module.models import User
from individual_module.models_wallet import IndividualWallet

u = User.objects.get(username='security_test_individual')
w = IndividualWallet.objects.filter(user=u)
print('Wallets for user:', w.count())
if w.exists():
    # Fix the corrupted balance first
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("UPDATE individual_module_individualwallet SET balance = 1000.00 WHERE user_id = %s AND balance = 999999999999.99", [u.id])
    print('Fixed corrupted balance to 1000.00')

    try:
        wallet = w.first()
        print('Wallet balance:', wallet.balance)
        print('Wallet type:', type(wallet.balance))
    except Exception as e:
        print('Error accessing balance:', e)
        # Try to get raw value from database
        cursor.execute("SELECT balance FROM individual_module_individualwallet WHERE user_id = %s", [u.id])
        raw_balance = cursor.fetchone()
        print('Raw balance from DB:', raw_balance)
