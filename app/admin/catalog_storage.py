"""Private upload staging and immutable, approved public catalog objects."""

import hashlib
import io
import warnings
from urllib.parse import quote

from PIL import Image, UnidentifiedImageError

from app.admin.source_storage import _request
from app.config.settings import get_settings

BUCKET = 'product-catalog'
STAGING = 'catalog-staging'
MAX_BYTES = 10 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 25_000_000


def ensure_buckets():
    buckets = {b['id']: b for b in _request('GET', 'bucket').json()}
    for name, public in ((BUCKET, True), (STAGING, False)):
        if name in buckets:
            if buckets[name].get('public') != public:
                raise ValueError('Catalog bucket access configuration does not match its purpose.')
        else:
            _request('POST', 'bucket', json={'id': name, 'name': name, 'public': public,
                'file_size_limit': MAX_BYTES, 'allowed_mime_types': ['image/png', 'image/jpeg']})


def inspect(content):
    if not content or len(content) > MAX_BYTES:
        raise ValueError('Choose a PNG or JPEG image up to 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in ('PNG', 'JPEG') or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Choose a still PNG or JPEG image.')
                width, height = image.size
                mime = 'image/png' if image.format == 'PNG' else 'image/jpeg'
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                image.load()
        if min(width, height) < 300:
            raise ValueError('Catalog images must be at least 300 pixels on each edge.')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('The image could not be safely decoded.') from None
    return {'sha256': hashlib.sha256(content).hexdigest(), 'mime_type': mime,
            'width': width, 'height': height, 'size_bytes': len(content)}


def public_url(key):
    return get_settings().supabase_url.rstrip('/') + '/storage/v1/object/public/' + BUCKET + '/' + quote(key, safe='/')


def signed_upload(identifier, extension):
    ensure_buckets()
    key = identifier + '.' + extension
    result = _request('POST', 'object/upload/sign/' + STAGING + '/' + key, json={'upsert': False}).json()
    relative = result.get('url') or result.get('signedURL')
    if not relative:
        raise RuntimeError('Storage did not return an image upload URL.')
    return key, get_settings().supabase_url.rstrip('/') + '/storage/v1' + relative


def _read(path):
    response = _request('GET', path, stream=True)
    try:
        content = bytearray()
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            if len(content) > MAX_BYTES:
                raise ValueError('Maximum image size is 10 MB.')
        return bytes(content)
    finally:
        response.close()


def read_upload(key):
    return _read('object/authenticated/' + STAGING + '/' + quote(key, safe=''))


def publish(asset_id, content):
    info = inspect(content)
    key = asset_id + '/' + info['sha256'] + ('.png' if info['mime_type'] == 'image/png' else '.jpg')
    ensure_buckets()
    path = BUCKET + '/' + quote(key, safe='/')
    try:
        existing = _read('object/public/' + path)
    except RuntimeError:
        _request('POST', 'object/' + path, data=content,
                 headers={'Content-Type': info['mime_type'], 'x-upsert': 'false', 'Cache-Control': '31536000'})
        existing = _read('object/public/' + path)
    if hashlib.sha256(existing).hexdigest() != info['sha256']:
        raise ValueError('Published image verification failed; previous active image was preserved.')
    return {**info, 'object_key': key}
