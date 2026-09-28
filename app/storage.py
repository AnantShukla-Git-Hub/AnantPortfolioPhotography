import os
import uuid

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "photos")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Mounted at this path in main.py — keep in sync with the StaticFiles mount.
PUBLIC_PATH_PREFIX = "/photos"

# Responsive size variants — target width in pixels; height scales to match
# the original aspect ratio. These three cover phone, tablet/laptop, and
# desktop/retina without ever sending a phone a full-resolution photo.
SIZE_VARIANTS = {
    "thumb": 480,
    "medium": 960,
    "full": 1800,
}


def _resize_to_width(image: Image.Image, target_width: int) -> Image.Image:
    if image.width <= target_width:
        return image  # never upscale — that makes it softer, not sharper
    ratio = target_width / image.width
    new_size = (target_width, max(1, round(image.height * ratio)))
    return image.resize(new_size, Image.LANCZOS)


def save_image(image: Image.Image) -> dict:
    """Saves 3 responsive variants of a watermarked PIL image to disk.
    Returns {"base_id": ..., "thumb": url, "medium": url, "full": url}."""
    base_id = uuid.uuid4().hex
    urls = {"base_id": base_id}
    for variant, width in SIZE_VARIANTS.items():
        resized = _resize_to_width(image, width)
        filename = f"{base_id}_{variant}.jpg"
        filepath = os.path.join(STORAGE_DIR, filename)
        resized.save(filepath, "JPEG", quality=85)
        urls[variant] = f"{PUBLIC_PATH_PREFIX}/{filename}"
    return urls


def delete_image(base_id: str) -> None:
    for variant in SIZE_VARIANTS:
        filepath = os.path.join(STORAGE_DIR, f"{base_id}_{variant}.jpg")
        if os.path.exists(filepath):
            os.remove(filepath)
