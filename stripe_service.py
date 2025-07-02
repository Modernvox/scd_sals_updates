import stripe
import logging
from flask import request, jsonify
from tenacity import retry, stop_after_attempt, wait_exponential
from config import PRICE_MAP, REVERSE_PRICE_MAP, TIER_LIMITS
import datetime

class StripeService:
    def __init__(self, stripe_secret_key, webhook_secret, db_manager, api_token):
        stripe.api_key = stripe_secret_key
        self.webhook_secret = webhook_secret
        self.db_manager = db_manager
        self.api_token = api_token
        logging.info("StripeService initialized")

    def create_checkout_session(self, tier, user_email, request_url_root):
        """
        Create a Stripe Checkout link only when the user explicitly provides an email.
        Until then, they remain on “free trial” and this method should not be called.
        """
        if not user_email:
            logging.info("User on free trial (no email), skipping checkout creation.")
            return {"error": "No email provided—user is still on free trial."}, 400

        if "@" not in user_email:
            logging.error(f"Invalid email: {user_email}")
            return {"error": "Invalid email address."}, 400

        if tier not in TIER_LIMITS:
            logging.error(f"Unknown tier requested: '{tier}'")
            return {"error": f"Invalid tier '{tier}'."}, 400

        try:
            current_count = self.db_manager.count_user_bins(user_email)
            max_bins = TIER_LIMITS[tier]["bins"]
            if current_count >= max_bins:
                logging.info(f"User {user_email} has {current_count} bins; max for {tier} is {max_bins}.")
                return {"error": f"Bin limit reached for tier '{tier}' ({max_bins} bins)."}, 400

            price_id = PRICE_MAP.get(tier)
            if not price_id:
                logging.error(f"No price ID configured for tier: {tier}")
                return {"error": f"No price found for tier '{tier}'"}, 400

            session = stripe.checkout.Session.create(
                success_url=request_url_root + 'success',
                cancel_url=request_url_root + 'cancel',
                payment_method_types=["card"],
                mode="subscription",
                customer_email=user_email,
                line_items=[{"price": price_id, "quantity": 1}],
                metadata={"user_email": user_email},
            )

            logging.info(f"Created Stripe Checkout Session for {user_email}, Tier: {tier}")
            return {"url": session.url}, 200

        except Exception as e:
            logging.error(f"Failed to create checkout session: {e}", exc_info=True)
            return {"error": "Internal server error"}, 500

    def verify_subscription(self, user_email, tier, license_key):
        """
        Called whenever the app needs to check if the stored subscription is still active.
        If license_key is empty or user_email is missing, we remain on “Trial.”
        """
        # If there is no license_key or no user_email, they stay on free‐trial
        if not user_email or not license_key:
            logging.info("No active subscription to verify; user stays on Trial.")
            return "Trial", ""

        try:
            subscription = stripe.Subscription.retrieve(license_key)
            status = subscription.get("status", "")
            # If subscription is not active/trialing, revert to Trial
            if status not in ("active", "trialing"):
                logging.info(
                    f"Subscription {license_key} is not active or trialing: status={status}. Reverting to Trial."
                )
                self.db_manager.update_subscription(user_email, "Trial", "")
                return "Trial", ""

            # If it is active, figure out which tier that price_id maps to:
            price_id = subscription["items"]["data"][0]["price"]["id"]
            new_tier = REVERSE_PRICE_MAP.get(price_id, "Trial")
            if new_tier != tier:
                logging.info(f"Updating tier from {tier} to {new_tier} for {user_email}")
                self.db_manager.update_subscription(user_email, new_tier, license_key)

            return new_tier, license_key

        except stripe.error.StripeError as e:
            logging.error(f"Failed to verify subscription: {e}", exc_info=True)
            # On any Stripe error, revert to Trial
            self.db_manager.update_subscription(user_email, "Trial", "")
            return "Trial", ""

    def handle_webhook(self, payload, signature):
        """
        Handle Stripe webhooks. If a user never upgraded, they will never appear here.
        If an event refers to a subscription, we update our DB accordingly.
        """
        logging.info("Stripe webhook received a request")
        try:
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)

            # -- Checkout Session Completed: user just purchased a subscription --
            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                sub_id = session.get("subscription")
                user_email = session.get("customer_email")

                if sub_id and user_email:
                    subscription = stripe.Subscription.retrieve(
                        sub_id, expand=["items.data.price"]
                    )
                    price_id = subscription["items"]["data"][0]["price"]["id"]
                    new_tier = REVERSE_PRICE_MAP.get(price_id, "Trial")
                    logging.info(f"Updating subscription to {new_tier} for {user_email}")
                    self.db_manager.update_subscription(user_email, new_tier, sub_id)

            # -- Subscription Updated: price/plan changed in Stripe Dashboard or via other means
            elif event["type"] == "customer.subscription.updated":
                subscription = event["data"]["object"]
                sub_id = subscription.get("id")
                price_id = subscription["items"]["data"][0]["price"]["id"]
                new_tier = REVERSE_PRICE_MAP.get(price_id, "Trial")

                # We need the corresponding user_email. We assume your DB can look it up via subscription ID.
                result = self.db_manager.load_subscription_by_id(sub_id)
                # load_subscription_by_id(...) should return (email, tier, license_key) or None
                if result:
                    user_email = result[0]
                    logging.info(f"Subscription updated to {new_tier} for {user_email}")
                    self.db_manager.update_subscription(user_email, new_tier, sub_id)

            # -- Subscription Deleted: user canceled from Stripe side
            elif event["type"] == "customer.subscription.deleted":
                # We only get the subscription ID in the payload
                subscription = event["data"]["object"]
                sub_id = subscription.get("id")
                # Look up which user_email that sub_id belonged to
                result = self.db_manager.load_subscription_by_id(sub_id)
                if result:
                    user_email = result[0]
                    logging.info(f"Subscription canceled for {user_email}. Reverting to Trial.")
                    self.db_manager.update_subscription(user_email, "Trial", "")

            # -- Payment Failed: subscription payment could not be collected
            elif event["type"] == "invoice.payment_failed":
                logging.info("Payment failed for subscription.")
                # You might choose to notify the user, but for now just acknowledge
                return 200, {"warning": "Payment failed"}

            return 200, ""

        except stripe.error.SignatureVerificationError as e:
            logging.error(f"Webhook signature verification failed: {e}", exc_info=True)
            return 400, ""
        except Exception as e:
            logging.error(f"Exception in stripe_webhook: {e}", exc_info=True)
            return 500, ""

    def downgrade_subscription(self, user_email, current_tier, new_tier, license_key):
        """
        If new_tier == "Trial", we cancel; otherwise we modify the existing subscription.
        If license_key is missing (user never upgraded), they are already on Trial—do nothing.
        """
        # Development mode bypass:
        if license_key == "DEV_MODE":
            if new_tier == current_tier:
                logging.info(f"(dev) No-op downgrade; already on {new_tier}")
                return False
            db_tier = "Trial" if new_tier == "Trial" else new_tier
            self.db_manager.update_subscription(user_email, db_tier, "DEV_MODE")
            logging.info(f"(dev) Downgraded to {db_tier}")
            return True

        # If the user is still on free trial (no subscription ID stored), there's nothing to downgrade:
        if not license_key or not user_email:
            logging.info("Downgrade attempt: No active subscription—already on Trial.")
            return False

        # If the user explicitly wants to go back to Trial:
        if new_tier == "Trial":
            return self.cancel_subscription(user_email, license_key)

        # Otherwise, modify the subscription’s price:
        try:
            subscription = stripe.Subscription.retrieve(license_key)
            price_id = PRICE_MAP.get(new_tier)
            if not price_id:
                logging.error(f"Invalid tier: {new_tier}")
                raise ValueError("Invalid tier")

            stripe.Subscription.modify(
                license_key,
                items=[{"id": subscription["items"]["data"][0]["id"], "price": price_id}],
            )
            self.db_manager.update_subscription(user_email, new_tier, license_key)
            logging.info(f"Downgraded to {new_tier} for {user_email}")
            return True

        except stripe.error.StripeError as e:
            logging.error(f"Downgrade failed: {e}", exc_info=True)
            raise
        except Exception as e:
            logging.error(f"Unexpected error in downgrade: {e}", exc_info=True)
            raise

    def cancel_subscription(self, user_email, license_key):
        """
        Delete the subscription in Stripe. If the user is still in free‐trial (no license_key),
        do nothing. If in DEV mode, just flip them back to Trial locally.
        """
        # Development mode:
        if license_key == "DEV_MODE":
            self.db_manager.update_subscription(user_email, "Trial", "")
            logging.info(f"(dev) Subscription cancelled for {user_email}")
            return True

        # If no subscription ID stored, they’re already on free trial:
        if not license_key or not user_email:
            logging.info("Cancel attempt: No active subscription—already on Trial.")
            return False

        try:
            stripe.Subscription.delete(license_key)
            self.db_manager.update_subscription(user_email, "Trial", "")
            logging.info(f"Subscription canceled for {user_email}")
            return True

        except stripe.error.StripeError as e:
            logging.error(f"Cancellation failed: {e}", exc_info=True)
            raise
        except Exception as e:
            logging.error(f"Unexpected error in cancel: {e}", exc_info=True)
            raise

    def get_subscription_status(self, license_key):
        """
        Return (status, next_billing_date) for a given license_key.
        If no license_key, always return ("N/A", "N/A").
        """
        # Development mode:
        if license_key == "DEV_MODE":
            return "Active", "N/A"

        # No subscription ID = free trial/no paid plan
        if not license_key:
            logging.info("No subscription ID provided for status check")
            return "N/A", "N/A"

        try:
            sub = stripe.Subscription.retrieve(license_key)
            status = sub.get("status", "").capitalize()
            ts = sub.get("trial_end") if status == "Trialing" else sub.get("current_period_end")
            if ts:
                next_billing_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            else:
                next_billing_date = "N/A"

            logging.info(
                f"Retrieved subscription status for {license_key}: "
                f"status={status}, next_billing={next_billing_date}"
            )
            return status, next_billing_date

        except stripe.error.InvalidRequestError as e:
            logging.error(f"Invalid subscription ID {license_key}: {e}", exc_info=True)
            return "N/A", "N/A"
        except stripe.error.StripeError as e:
            logging.error(f"Stripe API error for subscription {license_key}: {e}", exc_info=True)
            return "Error", "N/A"
        except Exception as e:
            logging.error(
                f"Unexpected error fetching subscription status for {license_key}: {e}",
                exc_info=True,
            )
            return "Error", "N/A"

    def create_test_subscription(self, user_email, tier):
        """
        For local testing: create a 7-day trial subscription in Stripe and store its ID.
        If user_email is missing, we can’t create one (they’re still on free trial).
        """
        if not user_email:
            logging.error(f"Invalid email: {user_email} (cannot create test subscription)")
            return None

        price_id = PRICE_MAP.get(tier)
        if not price_id:
            logging.error(f"Invalid tier: {tier}")
            return None

        try:
            # Find or create the Customer
            customers = stripe.Customer.list(email=user_email, limit=1)
            if customers.data:
                customer_id = customers.data[0].id
            else:
                customer = stripe.Customer.create(email=user_email)
                customer_id = customer.id

            # Create the subscription with a short trial
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="error_if_incomplete",
                trial_period_days=7,
                expand=["items.data.price"],
            )
            logging.info(f"Created test subscription for {user_email}: {subscription.id}")

            # Persist into your local database
            self.db_manager.update_subscription(user_email, tier, subscription.id)
            return subscription.id

        except stripe.error.StripeError as e:
            logging.error(f"Failed to create test subscription: {e}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"Unexpected error in test subscription: {e}", exc_info=True)
            return None
