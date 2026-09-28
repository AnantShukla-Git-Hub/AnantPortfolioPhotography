from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.models import Photo, get_session

router = APIRouter(prefix="/api/photos", tags=["photos"])


def _serialize(p: Photo) -> dict:
    return {
        "id": p.id,
        "url": p.url,
        "url_medium": p.url_medium,
        "url_thumb": p.url_thumb,
        "caption": p.caption,
    }


@router.get("")
def list_gallery_photos(session: Session = Depends(get_session)):
    photos = session.exec(
        select(Photo).order_by(Photo.gallery_order, Photo.uploaded_at)
    ).all()
    return [_serialize(p) for p in photos]


@router.get("/featured")
def list_featured_photos(session: Session = Depends(get_session)):
    photos = session.exec(
        select(Photo)
        .where(Photo.is_featured == True)  # noqa: E712
        .order_by(Photo.featured_order, Photo.uploaded_at)
    ).all()
    return [_serialize(p) for p in photos]
