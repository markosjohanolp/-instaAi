# image_generator.py
# ============================================================
# توليد الصور الكامل — 5 قوالب + شعار + QR
# ============================================================

import os
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper
from bidi.algorithm import get_display
import qrcode

# ============================================================
# الإعدادات
# ============================================================

BASE_DIR = os.path.dirname(__file__)
FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoKufiArabic.ttf")
OUTPUT_DIR = os.path.join(BASE_DIR, "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH = 1080
HEIGHT = 1080

# ============================================================
# القوالب (5 قوالب)
# ============================================================

TEMPLATES = {
    "classic": {
        "bg_type": "solid",
        "bg_color": (15, 15, 25),
        "text_color": (255, 255, 255),
        "accent_color": (200, 200, 200),
        "font_size": 75,
        "text_shadow": True,
    },
    "dark": {
        "bg_type": "gradient",
        "bg_color1": (10, 10, 20),
        "bg_color2": (40, 40, 70),
        "text_color": (255, 255, 255),
        "accent_color": (150, 150, 200),
        "font_size": 75,
        "text_shadow": True,
    },
    "gold": {
        "bg_type": "gradient",
        "bg_color1": (40, 30, 10),
        "bg_color2": (90, 70, 20),
        "text_color": (255, 240, 200),
        "accent_color": (255, 215, 0),
        "font_size": 75,
        "text_shadow": True,
    },
    "gradient": {
        "bg_type": "gradient",
        "bg_color1": (102, 126, 234),
        "bg_color2": (118, 75, 162),
        "text_color": (255, 255, 255),
        "accent_color": (255, 255, 255),
        "font_size": 75,
        "text_shadow": True,
    },
    "minimal": {
        "bg_type": "solid",
        "bg_color": (245, 245, 245),
        "text_color": (20, 20, 30),
        "accent_color": (100, 100, 100),
        "font_size": 75,
        "text_shadow": False,
    },
}


# ============================================================
# أدوات النص
# ============================================================

def reshape_arabic(text):
    """تشكيل النص العربي للعرض الصحيح"""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def wrap_text(text, font, max_width):
    """قسّم النص على أسطر حسب العرض"""
    lines = []
    words = text.split()
    current = ""

    for word in words:
        test = current + " " + word if current else word
        try:
            bbox = font.getbbox(test)
            width = bbox[2] - bbox[0]
        except Exception:
            width = len(test) * 30

        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


# ============================================================
# الخلفيات
# ============================================================

def make_gradient_bg(width, height, color1, color2):
    """خلفية متدرجة عمودية"""
    bg = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(bg)
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return bg


def make_solid_bg(width, height, color):
    """خلفية سادة"""
    return Image.new("RGB", (width, height), color)


def add_pattern(bg, accent_color, opacity=15):
    """يضيف نمط هندسي خفيف للخلفية"""
    draw = ImageDraw.Draw(bg, "RGBA")
    # نقاط صغيرة
    for _ in range(80):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        r = random.randint(2, 6)
        draw.ellipse([x, y, x + r, y + r],
                     fill=(*accent_color, opacity))
    return bg


# ============================================================
# تحميل الشعار
# ============================================================

def download_logo(logo_url):
    """حمّل شعار القناة من URL"""
    if not logo_url:
        return None
    try:
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo = Image.open(BytesIO(response.content)).convert("RGBA")
            logo.thumbnail((150, 150), Image.LANCZOS)
            return logo
    except Exception as e:
        print(f"[logo] {e}")
    return None


# ============================================================
# QR Code
# ============================================================

def make_qr_code(url, size=120):
    """ينشئ QR Code لرابط"""
    if not url:
        return None
    try:
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="white", back_color="black")
        qr_img = qr_img.convert("RGBA")
        qr_img = qr_img.resize((size, size), Image.LANCZOS)
        return qr_img
    except Exception as e:
        print(f"[qr] {e}")
        return None


# ============================================================
# توليد الصورة
# ============================================================

def generate_image(text, channel_username="", channel_title="",
                   logo_url=None, channel_link=None, template=None):
    """
    يولّد الصورة الكاملة.
    يرجع مسار الملف.
    """
    # اختر قالب عشوائي إذا مو محدد
    if template is None:
        template = random.choice(list(TEMPLATES.keys()))
    if template not in TEMPLATES:
        template = "gradient"

    cfg = TEMPLATES[template]

    # ===== الخلفية =====
    if cfg["bg_type"] == "gradient":
        bg = make_gradient_bg(WIDTH, HEIGHT,
                              cfg["bg_color1"], cfg["bg_color2"])
    else:
        bg = make_solid_bg(WIDTH, HEIGHT, cfg["bg_color"])

    # أضف نمط خفيف
    bg = add_pattern(bg, cfg["accent_color"], opacity=10)

    draw = ImageDraw.Draw(bg, "RGBA")

    # ===== الشعار (أعلى اليمين) =====
    logo = download_logo(logo_url)
    if logo:
        logo_x = WIDTH - logo.width - 40
        logo_y = 40
        bg.paste(logo, (logo_x, logo_y), logo)

    # ===== QR Code (أعلى اليسار) =====
    if channel_link:
        qr = make_qr_code(channel_link, size=120)
        if qr:
            bg.paste(qr, (40, 40), qr)

    # ===== النص الرئيسي =====
    try:
        font = ImageFont.truetype(FONT_PATH, cfg["font_size"])
        small_font = ImageFont.truetype(FONT_PATH, 32)
        title_font = ImageFont.truetype(FONT_PATH, 36)
    except Exception as e:
        print(f"[font] {e}")
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # شكّل النص
    shaped_text = reshape_arabic(text)

    # قسّم النص
    max_width = WIDTH - 200
    lines = wrap_text(shaped_text, font, max_width)

    # احسب الإحداثيات
    line_height = cfg["font_size"] + 30
    total_height = len(lines) * line_height
    start_y = (HEIGHT - total_height) // 2

    # ارسم النص
    for i, line in enumerate(lines):
        try:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
        except Exception:
            text_width = len(line) * 30

        x = (WIDTH - text_width) // 2
        y = start_y + (i * line_height)

        # ظل
        if cfg["text_shadow"]:
            draw.text((x + 3, y + 3), line,
                      font=font, fill=(0, 0, 0, 150))
        # النص
        draw.text((x, y), line, font=font, fill=cfg["text_color"])

    # ===== عنوان القناة (أسفل) =====
    if channel_title:
        shaped_title = reshape_arabic(channel_title)
        try:
            bbox = title_font.getbbox(shaped_title)
            text_width = bbox[2] - bbox[0]
        except Exception:
            text_width = len(shaped_title) * 20

        x = (WIDTH - text_width) // 2
        y = HEIGHT - 120

        if cfg["text_shadow"]:
            draw.text((x + 2, y + 2), shaped_title,
                      font=title_font, fill=(0, 0, 0, 150))
        draw.text((x, y), shaped_title,
                  font=title_font, fill=cfg["accent_color"])

    # ===== يوزر القناة (أسفل جداً) =====
    if channel_username:
        shaped_user = reshape_arabic(channel_username)
        try:
            bbox = small_font.getbbox(shaped_user)
            text_width = bbox[2] - bbox[0]
        except Exception:
            text_width = len(shaped_user) * 15

        x = (WIDTH - text_width) // 2
        y = HEIGHT - 70

        if cfg["text_shadow"]:
            draw.text((x + 2, y + 2), shaped_user,
                      font=small_font, fill=(0, 0, 0, 150))
        draw.text((x, y), shaped_user,
                  font=small_font, fill=cfg["accent_color"])

    # ===== احفظ =====
    filename = os.path.join(OUTPUT_DIR,
                            f"img_{random.randint(100000, 999999)}.png")
    bg.save(filename, "PNG", optimize=True)

    return filename