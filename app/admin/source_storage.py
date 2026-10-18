"""Private originals; only scoped upload/download URLs cross the admin boundary."""

from urllib.parse import quote

import requests

from app.config.settings import get_settings

BUCKET = "knowledge-originals"
MAX_BYTES = 10 * 1024 * 1024


def _request(method, path, **kwargs):
    settings = get_settings()
    secret = settings.supabase_secret_key or settings.supabase_service_role_key
    if not settings.supabase_url or not secret:
        raise ValueError(
            "Configure SUPABASE_URL and SUPABASE_SECRET_KEY on the backend first."
        )
    try:
        response = requests.request(
            method,
            settings.supabase_url.rstrip("/") + "/storage/v1/" + path,
            headers={
                "Authorization": "Bearer " + secret,
                "apikey": secret,
                **kwargs.pop("headers", {}),
            },
            timeout=(5, 30),
            **kwargs,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        code = (
            error.response.status_code if error.response is not None else "unavailable"
        )
        raise RuntimeError(
            f"Private file storage returned {code}; inspect backend credentials/connectivity."
        ) from None


def ensure_bucket():
    buckets = _request("GET", "bucket").json()
    bucket = next((b for b in buckets if b["id"] == BUCKET), None)
    if bucket:
        if bucket.get("public"):
            raise ValueError("The knowledge-originals bucket must be private.")
        return
    _request(
        "POST",
        "bucket",
        json={
            "id": BUCKET,
            "name": BUCKET,
            "public": False,
            "file_size_limit": MAX_BYTES,
            "allowed_mime_types": ["application/pdf", "text/plain"],
        },
    )


def object_key(path):
    return BUCKET + "/" + quote(path, safe="/")


def signed_upload(path):
    ensure_bucket()
    result = _request(
        "POST", "object/upload/sign/" + object_key(path), json={"upsert": False}
    ).json()
    relative = result.get("url") or result.get("signedURL")
    if not relative:
        raise RuntimeError("Storage did not return an upload URL.")
    return get_settings().supabase_url.rstrip("/") + "/storage/v1" + relative


def signed_download(path):
    result = _request(
        "POST", "object/sign/" + object_key(path), json={"expiresIn": 300}
    ).json()
    return get_settings().supabase_url.rstrip("/") + "/storage/v1" + result["signedURL"]


def read(path):
    response = _request("GET", "object/authenticated/" + object_key(path), stream=True)
    try:
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > MAX_BYTES:
                raise ValueError("Maximum file size is 10 MB.")
        return bytes(data)
    finally:
        response.close()


def write(path, content, content_type):
    ensure_bucket()
    _request(
        "POST",
        "object/" + object_key(path),
        data=content,
        headers={"Content-Type": content_type, "x-upsert": "false"},
    )


def remove(path):
    _request("DELETE", "object/" + BUCKET, json={"prefixes": [path]})
