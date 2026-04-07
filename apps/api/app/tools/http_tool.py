import requests


def safe_http_get(url: str, timeout: int = 15) -> dict:
    response = requests.get(url, timeout=timeout)
    return {
        "status": "success",
        "action": "http_request",
        "url": url,
        "status_code": response.status_code,
        "content_preview": response.text[:1000],
    }
