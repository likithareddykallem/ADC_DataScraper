import time

import requests

from config import HTTP_TIMEOUT_SECONDS


def get(url, **kwargs):
    timeout = kwargs.pop("timeout", HTTP_TIMEOUT_SECONDS)
    last_error = None
    for attempt in range(3):
        try:
            if attempt:
                time.sleep(0.5 * attempt)
            response = requests.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
    raise last_error
