from dailywage_module.models_wallet import DailyWageWallet
from decimal import Decimal, InvalidOperation

print("Checking all DailyWageWallet balances...")
for w in DailyWageWallet.objects.all():
    try:
        print(f"Wallet {w.id}: balance = {w.balance}")
    except Exception as e:
        print(f"Error in wallet {w.id}: {e}")

print("\nFixing invalid balances...")
for w in DailyWageWallet.objects.all():
    try:
        _ = Decimal(str(w.balance))
    except (InvalidOperation, TypeError):
        print(f"Fixing wallet {w.id} invalid balance: {w.balance}")
        w.balance = Decimal('0.00')
        w.save()

print("Done.")
