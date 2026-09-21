# app.py
# ============================================================
# خدمة إنستكرام — كامل
# ============================================================

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from image_generator import generate_image
from instagram_handler import (
    post_photo, post_carousel, check_account,
    login_instagram
)

app = Flask(__name__)
CORS(app)


# ============================================================
# Health
# ============================================================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "ok": True,
        "service": "Instagram Service",
        "version": "2.0",
        "status": "running"
    })


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# ============================================================
# نشر
# ============================================================

@app.route("/publish", methods=["POST"])
def publish():
    """
    Body:
    {
        "text": "نص المنشور",
        "channel_username": "@channel",
        "channel_title": "اسم القناة",
        "channel_link": "https://t.me/channel",
        "logo_url": "https://...",
        "post_id": 123,
        "instagram_username": "user",
        "instagram_password": "pass",
        "hashtags": "#tag1 #tag2",
        "template": "gradient"  // اختياري
    }
    """
    data = request.get_json(silent=True) or {}

    text = data.get("text", "").strip()
    channel_username = data.get("channel_username", "").strip()
    channel_title = data.get("channel_title", "").strip()
    channel_link = data.get("channel_link", "").strip()
    logo_url = data.get("logo_url", "").strip()
    hashtags = data.get("hashtags", "").strip()
    template = data.get("template")

    instagram_username = data.get("instagram_username", "").strip()
    instagram_password = data.get("instagram_password", "").strip()

    # التحقق
    if not text:
        return jsonify({"ok": False, "error": "النص مطلوب"}), 400
    if not instagram_username or not instagram_password:
        return jsonify({"ok": False, "error": "بيانات إنستكرام مطلوبة"}), 400

    # 1. ولّد الصورة
    try:
        image_path = generate_image(
            text=text,
            channel_username=channel_username,
            channel_title=channel_title,
            logo_url=logo_url,
            channel_link=channel_link,
            template=template
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"فشل توليد الصورة: {e}"}), 500

    # 2. جهّز الكابشن
    caption_parts = [text]

    if channel_username:
        caption_parts.append(f"\n📢 {channel_username}")
    if channel_link:
        caption_parts.append(f"🔗 {channel_link}")
    if hashtags:
        caption_parts.append(f"\n{hashtags}")

    caption = "\n".join(caption_parts)

    # 3. انشر
    success, error = post_photo(
        instagram_username,
        instagram_password,
        image_path,
        caption
    )

    # 4. نظّف الصورة
    try:
        os.remove(image_path)
    except Exception:
        pass

    if success:
        return jsonify({"ok": True, "message": "تم النشر"})
    else:
        return jsonify({"ok": False, "error": error}), 500


# ============================================================
# فحص حساب
# ============================================================

@app.route("/check", methods=["POST"])
def check():
    """
    Body: {"username": "...", "password": "..."}
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"ok": False, "error": "بيانات ناقصة"}), 400

    success, result = check_account(username, password)
    if success:
        return jsonify({"ok": True, "data": result})
    return jsonify({"ok": False, "error": result}), 500


# ============================================================
# توليد صورة فقط (بدون نشر)
# ============================================================

@app.route("/preview", methods=["POST"])
def preview():
    """
    يولّد صورة فقط — للمعاينة.
    Body: {
        "text": "...",
        "channel_username": "...",
        "channel_title": "...",
        "channel_link": "...",
        "logo_url": "...",
        "template": "..."
    }
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"ok": False, "error": "النص مطلوب"}), 400

    try:
        image_path = generate_image(
            text=text,
            channel_username=data.get("channel_username", ""),
            channel_title=data.get("channel_title", ""),
            logo_url=data.get("logo_url", ""),
            channel_link=data.get("channel_link", ""),
            template=data.get("template")
        )
        return jsonify({
            "ok": True,
            "data": {"image_path": image_path}
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ============================================================
# تشغيل
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)