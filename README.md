# Anant Shukla — Photography Portfolio

A small portfolio for the photographs I take. The public site is a fast, static page; photos are uploaded through a private admin panel that only runs on my own computer.

Live on: https://anant-portfolio-photography.vercel.app/

## How it works

The deployed site is static: HTML, CSS, JavaScript, the watermarked photos and a `photos.json` file. It has no server, database, login or upload endpoint.

Uploading happens locally. A FastAPI admin panel runs on my computer, `export_static.py` copies the finished photos and `photos.json` into `public/`, and pushing to GitHub lets Vercel publish the update.

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

## Credits and license

- Fraunces and Inter, loaded from Google Fonts (SIL Open Font License)
- Mr De Haviland, bundled in `app/fonts/` (SIL Open Font License, see `OFL.txt`)

Photographs and written content © 2026 Anant Shukla. All rights reserved.
