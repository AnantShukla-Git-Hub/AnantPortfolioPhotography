# Anant Shukla — Photography Portfolio

A small portfolio for the photographs I take. The public site is a fast, static page; photos are uploaded through a private admin panel that only runs on my own computer.

Live site: _add the Vercel link here after the first deploy_

## Highlights

- Rotating 3D carousel of featured photos (mouse wheel, drag or swipe), with a full-screen viewer
- Masonry gallery that keeps every photo in its original aspect ratio, with optional captions
- Light and dark themes with a glass-style interface
- Responsive images: three sizes are generated per upload, so phones load small files and large screens stay sharp
- Every upload gets a small handwritten signature in the bottom-right corner and has its EXIF metadata removed

## How it works

The deployed site is static: HTML, CSS, JavaScript, the watermarked photos and a `photos.json` file. It has no server, database, login or upload endpoint.

Uploading happens locally. A FastAPI admin panel runs on my computer, `export_static.py` copies the finished photos and `photos.json` into `public/`, and pushing to GitHub lets Vercel publish the update.

```
app/                     FastAPI admin backend (local use only)
  routers/               photo and admin API routes
  fonts/                 signature font used for the watermark (SIL OFL)
static/                  admin panel page, served at /admin-ui/
public/                  the deployed site (Vercel root directory)
export_static.py         writes photos, photos.json and og-image.jpg into public/
set_admin_password.py    changes the local admin password
requirements.txt
```

## Run the admin panel locally

Requires Python 3.10+.

```
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

set ADMIN_PASSWORD=choose-a-long-password     # macOS/Linux: export ADMIN_PASSWORD=...
uvicorn app.main:app --reload
```

- Site preview: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin-ui/

`ADMIN_PASSWORD` is only read when the database is first created. To change the password later, run `python set_admin_password.py`. Never start the server with `--host 0.0.0.0`; the admin panel is meant for this computer only.

## Publish an update

1. Upload photos in the admin panel and mark the featured ones.
2. `python export_static.py`
3. `git add .`, `git commit -m "Add photos"`, `git push`

Vercel settings: Root Directory `public`, Framework Preset "Other", no build command.

## Security notes

- Nothing in the deployed site can accept input, so there is nothing to log in to or upload through.
- The database, original uploads, virtual environment and secret key are excluded by `.gitignore`.
- Only resized, watermarked photos (at most 1800 px wide) are published.

## Credits and license

- Fraunces and Inter, loaded from Google Fonts (SIL Open Font License)
- Mr De Haviland, bundled in `app/fonts/` (SIL Open Font License, see `OFL.txt`)

Photographs and written content © 2026 Anant Shukla. All rights reserved.
