# TODO: Add alert_threshold field to CoupleWallet model

## Steps to complete:

1. **Edit models_wallet.py**: Add the `alert_threshold` field to the `CoupleWallet` model in `couple_module/models_wallet.py`.
   - Field: `alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Threshold for low balance alerts")`
   - Place it after the existing fields, before the Meta class.
   - [x] Completed: Field added successfully.

2. **Create Django migration**: Run `python manage.py makemigrations couple_module` to generate the migration file for the new field.
   - [x] Completed: Migration 0004_couplewallet_alert_threshold_and_more.py created successfully.

3. **Apply migration**: Run `python manage.py migrate couple_module` to update the database schema.
   - [x] Completed: Migration applied successfully.

4. **Verify the change**:
   - Check the migration file in `couple_module/migrations/` to confirm it adds the field.
   - Optionally, inspect the database or run a test to ensure the field is added.
   - [x] Completed: Migration file confirmed to add alert_threshold field correctly.

5. **Update documentation or tests if needed**: Review if any views, forms, or tests need updates to use the new field (none identified in plan).
   - [x] Completed: No updates needed.

6. **Mark task complete**: Update this TODO.md with completion status and close the task.
   - [x] Completed: Task fully implemented.
