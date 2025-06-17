#!/usr/bin/env python3
"""
Polls a specified endpoint every 10 minutes ±2 minutes.
Logs responses with empty payloads to `empty_responses.log` and with non-empty payloads to `non_empty_responses.log`.
Each log entry includes a timestamp, status code, and the full payload.
Requires: requests
"""

import time
import random
import requests
from datetime import datetime
import json

# Configuration
ENDPOINT_URL = (
    "https://api.waitwhile.com/v2/public/visits/cornwallsamplestore/first-available-slots"
)
BASE_INTERVAL = 10 * 60       # 10 minutes in seconds
VARIATION = 2 * 60            # ±2 minutes in seconds

# Log file names
EMPTY_LOG = "empty_responses.log"
NON_EMPTY_LOG = "non_empty_responses.log"


def log_to_file(filename: str, message: str) -> None:
    """Appends a log message to the given file with a newline."""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(message + "\n")


def build_log_entry(status_code: int, payload) -> str:
    timestamp = datetime.utcnow().isoformat()
    # Serialize payload to a JSON string
    try:
        if isinstance(payload, (dict, list)):
            payload_str = json.dumps(payload, ensure_ascii=False)
        else:
            # If it's a string, try to parse it as JSON first
            try:
                parsed = json.loads(payload)
                payload_str = json.dumps(parsed, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                # If it's not valid JSON, just use the string as is
                payload_str = str(payload)
    except Exception as e:
        # Fallback in case of any serialization issues
        payload_str = f"Error serializing payload: {str(e)}"
    
    return f"{timestamp} - Status code: {status_code} - Payload: {payload_str}"


def poll_endpoint() -> None:
    """Continuously polls the endpoint and logs responses based on payload size."""
    while True:
        try:
            response = requests.get(ENDPOINT_URL)
            status = response.status_code
            try:
                data = response.json()
            except ValueError:
                # Non-JSON or invalid JSON
                data = response.text

            log_entry = build_log_entry(status, data)
            # Check for an empty list payload
            if isinstance(data, list) and len(data) == 0:
                log_to_file(EMPTY_LOG, log_entry)
            else:
                log_to_file(NON_EMPTY_LOG, log_entry)

        except requests.RequestException as e:
            error_entry = f"{datetime.utcnow().isoformat()} - Request failed: {e}"
            log_to_file(NON_EMPTY_LOG, error_entry)

        # Sleep for 10 minutes ± 2 minutes
        delay = BASE_INTERVAL + random.uniform(-VARIATION, VARIATION)
        time.sleep(delay)


if __name__ == "__main__":
    poll_endpoint() 