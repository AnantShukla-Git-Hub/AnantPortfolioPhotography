"""Run on YOUR PC before every `git push`:

    python export_static.py

It reads your local admin database and writes everything the static site needs into
public/: the watermarked photos, photos.json (captions, featured list) and og-image.jpg
(the preview picture LinkedIn shows). The backend, database and admin panel are never
part of the deployed site.
"""
import colorsys
import hashlib
import json
import os
import re
import shutil
import sys

from PIL import Image
from sqlmodel import Session, select

# >>> After your first Vercel deploy, put your real site address here (once). <<<
SITE_URL = os.environ.get("SITE_URL", "https://anant-portfolio-photography.vercel.app").rstrip("/")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from app.models import DB_PATH, Photo, engine  # noqa: E402

SRC_DIR = os.path.join(ROOT, "storage", "photos")
OUT_DIR = os.path.join(ROOT, "public")
OUT_PHOTOS = os.path.join(OUT_DIR, "photos")
INDEX_HTML = os.path.join(OUT_DIR, "index.html")
PROFILE_SRC = os.path.join(ROOT, "storage", "profile.jpg")           # uploaded in the admin panel
PROFILE_OUT = os.path.join(OUT_DIR, "assets", "anant-profile.jpg")   # shown in the About section


def visual_meta(p):
    """Layout ratio (r), real ratio (rr) and two accent colours (c, c2) for the new design."""
    with Image.open(os.path.join(SRC_DIR, os.path.basename(p.url))) as im:
        w, h = im.size
    ratio = w / h
    r = "3/2" if ratio > 1.25 else ("4/5" if ratio < 0.9 else "1/1")
    with Image.open(os.path.join(SRC_DIR, os.path.basename(p.url_thumb))) as t:
        R, G, B = t.convert("RGB").resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    hue, sat, val = colorsys.rgb_to_hsv(R / 255, G / 255, B / 255)
    sat = min(1, max(sat, 0.45) * 1.1)
    v1 = min(0.85, max(val, 0.6))
    v2 = max(0.28, v1 * 0.5)

    def hx(*hsv):
        return "#%02x%02x%02x" % tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))

    return {"r": r, "rr": f"{w}/{h}", "c": hx(hue, sat, v1), "c2": hx(hue, min(1, sat + 0.1), v2)}


def serialize(p):
    return {
        "id": p.id,
        "url": p.url,
        "url_medium": p.url_medium,
        "url_thumb": p.url_thumb,
        "caption": p.caption,
        **visual_meta(p),
    }


def make_og_image(candidates):
    """1200x630 centre crop of the first landscape photo (or the first photo)."""
    if not candidates:
        return False
    chosen = None
    for p in candidates:
        path = os.path.join(OUT_PHOTOS, os.path.basename(p["url"]))
        with Image.open(path) as im:
            if im.width >= im.height:
                chosen = path
                break
    chosen = chosen or os.path.join(OUT_PHOTOS, os.path.basename(candidates[0]["url"]))
    with Image.open(chosen) as im:
        im = im.convert("RGB")
        target = 1200 / 630
        w, h = im.size
        if w / h > target:
            new_w = int(h * target)
            box = ((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h)
        else:
            new_h = int(w / target)
            box = (0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h)
        im.crop(box).resize((1200, 630), Image.LANCZOS).save(
            os.path.join(OUT_DIR, "og-image.jpg"), "JPEG", quality=85
        )
    return True


def export_profile():
    """Copy the admin-uploaded profile photo (if there is one) into public/assets and describe it.
    The site reads this from photos.json, so the About frame always fits the photo."""
    if os.path.exists(PROFILE_SRC):
        os.makedirs(os.path.dirname(PROFILE_OUT), exist_ok=True)
        shutil.copy2(PROFILE_SRC, PROFILE_OUT)
    if not os.path.exists(PROFILE_OUT):
        return None
    with open(PROFILE_OUT, "rb") as f:
        version = hashlib.md5(f.read()).hexdigest()[:8]  # changes when the photo changes -> no stale cache
    with Image.open(PROFILE_OUT) as im:
        w, h = im.size
    return {"url": "/assets/anant-profile.jpg", "rr": f"{w}/{h}", "v": version}


def set_meta(html, attr, key, value):
    pattern = re.compile(r'(<meta\s+' + attr + r'="' + re.escape(key) + r'"\s+content=")[^"]*(")')
    return pattern.sub(lambda m: m.group(1) + value + m.group(2), html)


def main():
    if not os.path.exists(DB_PATH):
        sys.exit("portfolio.db not found. Run this from the project folder, after uploading photos in the admin panel.")

    with Session(engine) as session:
        gallery_rows = session.exec(select(Photo).order_by(Photo.gallery_order, Photo.uploaded_at)).all()
        featured_rows = session.exec(
            select(Photo).where(Photo.is_featured == True)  # noqa: E712
            .order_by(Photo.featured_order, Photo.uploaded_at)
        ).all()
        gallery = [serialize(p) for p in gallery_rows]
        featured = [serialize(p) for p in featured_rows]

    os.makedirs(OUT_PHOTOS, exist_ok=True)
    needed = set()
    for p in gallery:
        for key in ("url", "url_medium", "url_thumb"):
            needed.add(os.path.basename(p[key]))

    for name in sorted(needed):
        src = os.path.join(SRC_DIR, name)
        if not os.path.exists(src):
            sys.exit(f"Missing file in storage/photos: {name}")
        shutil.copy2(src, os.path.join(OUT_PHOTOS, name))
        with Image.open(src) as im:
            if len(im.getexif()) > 0:
                print(f"WARNING: {name} still carries EXIF metadata (location/camera info)")

    removed = 0
    for name in os.listdir(OUT_PHOTOS):
        if name not in needed:
            os.remove(os.path.join(OUT_PHOTOS, name))
            removed += 1

    with open(os.path.join(OUT_DIR, "photos.json"), "w", encoding="utf-8") as f:
        json.dump({"gallery": gallery, "featured": featured, "profile": export_profile()}, f, ensure_ascii=False, indent=1)

    og_ok = make_og_image(featured + gallery)

    with open(INDEX_HTML, encoding="utf-8") as f:
        html = f.read()
    html = set_meta(html, "property", "og:url", SITE_URL + "/")
    html = set_meta(html, "property", "og:image", SITE_URL + "/og-image.jpg")
    html = set_meta(html, "name", "twitter:image", SITE_URL + "/og-image.jpg")
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Exported {len(gallery)} photos ({len(featured)} featured), removed {removed} stale files.")
    print("og-image.jpg:", "created" if og_ok else "skipped (no photos yet)")
    if "YOUR-SITE" in SITE_URL:
        print("NOTE: SITE_URL is still the placeholder. Set your real address in export_static.py after the first deploy.")


if __name__ == "__main__":
    main()
