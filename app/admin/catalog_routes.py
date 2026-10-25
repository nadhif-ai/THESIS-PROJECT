import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.admin import catalog, catalog_storage, store
from app.config.settings import get_settings

router = APIRouter(prefix='/catalog', tags=['Product catalog'])


def visible(data):
    return {**data, 'url': catalog_storage.public_url(data['object_key'])}


@router.get('')
def catalog_list():
    data = catalog.snapshot()
    return {**data, 'assets': [visible(a) for a in data['assets']]}


@router.get('/export')
def export_catalog():
    return {'format': 'product-catalog-v1', **catalog.snapshot()}


class Feature(BaseModel):
    enabled: bool = Field(strict=True)


@router.put('/feature')
def feature(body: Feature):
    store.catalog_feature(body.enabled)
    return {'enabled': body.enabled}


class Upload(BaseModel):
    mime_type: str = Field(pattern=r'^image/(png|jpeg)$')
    size_bytes: int = Field(gt=0, le=catalog_storage.MAX_BYTES)


@router.post('/uploads')
def upload(body: Upload):
    identifier = uuid.uuid4().hex
    try:
        key, url = catalog_storage.signed_upload(identifier, 'png' if body.mime_type == 'image/png' else 'jpg')
        store.catalog_stage_upload(identifier, key, body.size_bytes)
        return {'upload_id': identifier, 'url': url}
    except (ValueError, RuntimeError) as error:
        raise HTTPException(503, str(error)) from None


class Save(catalog.AssetEdit):
    expected_revision: int = Field(ge=0)
    upload_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')


@router.put('/assets/{asset_id}')
def save_asset(asset_id: str, body: Save):
    if asset_id != body.asset_id:
        raise HTTPException(400, 'The asset identity must match its URL.')
    try:
        old = next((a for a in catalog.snapshot()['assets'] if a['asset_id'] == asset_id), {})
        if old.get('revision', 0) != body.expected_revision:
            raise catalog.Conflict('This image changed. Reload before saving again.')
        info = {k: old[k] for k in ('object_key','sha256','mime_type','width','height','size_bytes','is_ai_generated','provenance') if k in old}
        if body.upload_id:
            ticket = store.catalog_upload(body.upload_id)
            content = catalog_storage.read_upload(ticket['object_key'])
            if len(content) != ticket['size_bytes']:
                raise ValueError('The uploaded image size does not match its ticket.')
            info.update(catalog_storage.publish(asset_id, content))
            info['is_ai_generated'] = old.get('is_ai_generated', False)
            info['provenance'] = {**old.get('provenance', {}), 'last_upload': body.upload_id}
        if not info.get('object_key'):
            raise ValueError('Upload an image before saving a new catalog asset.')
        fields = body.model_dump(exclude={'expected_revision','upload_id'})
        for key, value in fields.items():
            if isinstance(value, list):
                fields[key] = [term.strip() for term in value if term.strip()]
        return visible(catalog.save({**info, **fields}, body.expected_revision, get_settings().admin_username))
    except catalog.Conflict as error:
        raise HTTPException(409, str(error)) from None
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    except RuntimeError:
        raise HTTPException(503, 'Image storage is unavailable. The previous active asset was preserved.') from None
