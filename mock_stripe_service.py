import logging

class MockStripeService:
    def __init__(self, stripe_secret_key, webhook_secret, db_manager, api_token):
        logging.info("Initialized MockStripeService for development")
        self.db_manager = db_manager  # Store for potential use

    def create_checkout_session(self, tier, user_email, url_root):
        logging.info(f"Mock: Creating checkout session for {user_email}, tier={tier}")
        return {"url": f"{url_root.rstrip('/')}/success?subscription_id=mock_sub_123"}, 200

    def handle_webhook(self, payload, signature):
        logging.info("Mock: Handling Stripe webhook")
        return 200, {"status": "mock_success"}

    def get_subscription_status(self, license_key):
        logging.info(f"Mock: Checking subscription status for license_key={license_key}")
        # Mock Gold tier status for development
        return "active", "N/A"  # (status, next_billing)

    def downgrade_subscription(self, user_email, current_tier, new_tier, license_key):
        logging.info(f"Mock: Downgrading subscription for {user_email} from {current_tier} to {new_tier}")
        return True  # Mock success

    def cancel_subscription(self, user_email, license_key):
        logging.info(f"Mock: Canceling subscription for {user_email}")
        return True  # Mock success
