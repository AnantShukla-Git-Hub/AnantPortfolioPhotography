import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Request
from PIL import Image, UnidentifiedImageError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, select

from app.models import Photo, get_session
from app.auth import authenticate_admin, create_access_token, require_admin, COOKIE_NAME
from app.watermark import apply_watermark
from app.storage import save_image, delete_image

router = APIRouter(prefix="/api/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if not authenticate_admin(username, password):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    token = create_access_token(username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=12 * 60 * 60,
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.post("/photos")
def upload_photo(
    file: UploadFile = File(...),
    caption: str = Form(None),
    is_featured: bool = Form(False),
    session: Session = Depends(get_session),
    _admin: str = Depends(require_admin),
):
    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 15MB)")

    try:
        image = Image.open(io.BytesIO(raw))
        image.load()  # forces Pillow to actually decode it, catching fakes
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="File is not a valid image")

    watermarked = apply_watermark(image)
    urls = save_image(watermarked)

    max_gallery_order = session.exec(select(Photo.gallery_order)).all()
    next_order = (max(max_gallery_order) + 1) if max_gallery_order else 0

    photo = Photo(
        base_id=urls["base_id"],
        url=urls["full"],
        url_medium=urls["medium"],
        url_thumb=urls["thumb"],
        caption=caption,
        is_featured=is_featured,
        gallery_order=next_order,
    )
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return {
        "id": photo.id, "url": photo.url, "url_medium": photo.url_medium,
        "url_thumb": photo.url_thumb, "caption": photo.caption, "is_featured": photo.is_featured,
    }


@router.patch("/photos/{photo_id}")
def update_photo(
    photo_id: int,
    caption: str = Form(None),
    is_featured: bool = Form(None),
    featured_order: int = Form(None),
    session: Session = Depends(get_session),
    _admin: str = Depends(require_admin),
):
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if caption is not None:
        photo.caption = caption
    if is_featured is not None:
        photo.is_featured = is_featured
    if featured_order is not None:
        photo.featured_order = featured_order
    session.add(photo)
    session.commit()
    return {"ok": True}


@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int,
    session: Session = Depends(get_session),
    _admin: str = Depends(require_admin),
):
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    delete_image(photo.base_id)
    session.delete(photo)
    session.commit()
    return {"ok": True}


@router.get("/photos")
def list_all_for_admin(session: Session = Depends(get_session), _admin: str = Depends(require_admin)):
    """Same as public list but includes everything, for the admin dashboard table."""
    photos = session.exec(select(Photo).order_by(Photo.uploaded_at.desc())).all()
    return [
        {
            "id": p.id, "url": p.url, "url_medium": p.url_medium, "url_thumb": p.url_thumb,
            "caption": p.caption, "is_featured": p.is_featured, "featured_order": p.featured_order,
            "gallery_order": p.gallery_order,
        }
        for p in photos
    ]
