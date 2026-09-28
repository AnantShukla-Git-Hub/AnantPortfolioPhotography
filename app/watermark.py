import os

from PIL import Image, ImageDraw, ImageFont

WATERMARK_TEXT = "Anant Shukla"

# Handwriting-style signature font, bundled with the project so it also works on
# Windows/Mac (system font paths differ per OS). Put the .ttf in app/fonts/.
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "MrDeHaviland-Regular.ttf")


def _load_font(size: int):
    """Bundled signature font first; plain system fonts / Pillow default only as a fallback."""
    candidates = [
        FONT_PATH,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def apply_watermark(image: Image.Image) -> Image.Image:
    """Returns a NEW image with a small handwritten-style 'Anant Shukla' signature
    in the bottom-right corner, like a painter signing a canvas."""
    image = image.convert("RGBA")
    width, height = image.size

    # signature fonts have a small x-height, so the size is larger than a normal label
    font_size = max(30, int(width * 0.042))
    font = _load_font(font_size)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    margin = max(12, int(min(width, height) * 0.025))
    x = width - text_w - margin - bbox[0]
    y = height - text_h - margin - bbox[1]

    # soft dark shadow so the signature stays readable on bright photos too
    shadow = max(1, font_size // 45)
    draw.text((x + shadow, y + shadow), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 85))
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 225))

    watermarked = Image.alpha_composite(image, overlay)
    return watermarked.convert("RGB")
