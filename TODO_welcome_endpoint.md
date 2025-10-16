# TODO: Add Welcome Endpoint to Couple Wallet

## Steps to Complete:
- [x] Add a new `@action(detail=False, methods=['get'])` method named `welcome` to the `CoupleWalletViewSet` in `views_wallet_final.py`
- [x] In the `welcome` method, log the request metadata (method and path) using `SecurityEventManager.log_event`
- [x] Return a JSON response with `{"message": "Welcome to the Couple Wallet API Service!"}`
- [x] Test the endpoint by making a GET request to the welcome URL

## Notes:
- The endpoint will be accessible at `/couple/wallet/welcome/` (assuming the URL pattern)
- Ensure the logging includes request.method and request.path
- Use the existing security and audit services for consistency
