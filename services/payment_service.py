import os
import hmac
import hashlib
import requests
from requests.auth import HTTPBasicAuth


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


PLANS = {
    "premium_monthly": {
        "name": "SAIVEX Premium Monthly",
        "amount": 19900,
        "currency": "INR",
        "days": 30
    },
    "premium_yearly": {
        "name": "SAIVEX Premium Yearly",
        "amount": 199900,
        "currency": "INR",
        "days": 365
    }
}


def create_razorpay_order(plan_id, user_id=None, email=""):
    if plan_id not in PLANS:
        return None, "Invalid plan."

    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None, "Razorpay keys missing. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env."

    plan = PLANS[plan_id]

    try:
        response = requests.post(
            "https://api.razorpay.com/v1/orders",
            auth=HTTPBasicAuth(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            json={
                "amount": plan["amount"],
                "currency": plan["currency"],
                "receipt": f"saivex_{plan_id}_{user_id or 'user'}",
                "notes": {
                    "product": "SAIVEX",
                    "plan": plan_id,
                    "user_id": str(user_id or ""),
                    "email": email or ""
                }
            },
            timeout=30
        )

        data = response.json()

        if response.status_code >= 400:
            return None, data

        return data, None

    except Exception as error:
        return None, str(error)


def verify_razorpay_signature(order_id, payment_id, signature):
    if not RAZORPAY_KEY_SECRET:
        return False

    msg = f"{order_id}|{payment_id}".encode("utf-8")
    secret = RAZORPAY_KEY_SECRET.encode("utf-8")
    expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, signature or "")
