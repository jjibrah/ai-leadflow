import hashlib
import hmac
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

secret = os.environ["WEBHOOK_SECRET"]

payload = {
    "name": "John Doe",
    "email": "john@acmelogistics.com",
    "company": "Acme Logistics",
    "message": "We need an ERP solution for our logistics company."
}

raw_body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")

timestamp = str(int(time.time()))

signing_payload = (
    timestamp.encode("utf-8")
    + b"."
    + raw_body
)

signature = hmac.new(
    secret.encode("utf-8"),
    signing_payload,
    hashlib.sha256,
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Webhook-Event-Id": "evt_test_001",
    "X-Webhook-Timestamp": timestamp,
    "X-Webhook-Signature": signature,
}

response = requests.post(
    "http://127.0.0.1:8000/api/webhooks/enquiries",
    data=raw_body,
    headers=headers,
)

print(response.status_code)
print(response.json())