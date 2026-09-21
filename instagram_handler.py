# instagram_handler.py
# ============================================================
# التعامل مع إنستكرام — كامل
# ============================================================

import os
import time
import json
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, ChallengeRequired,
    PleaseWaitFewMinutes, RateLimitError
)

BASE_DIR = os.path.dirname(__file__)
SESSION_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY = 60  # ثانية


# ============================================================
# الجلسات
# ============================================================

def get_session_path(username):
    return os.path.join(SESSION_DIR, f"{username}.json")


def save_session(cl, username):
    try:
        path = get_session_path(username)
        cl.dump_settings(path)
    except Exception as e:
        print(f"[session save] {e}")


def load_session(cl, username):
    try:
        path = get_session_path(username)
        if os.path.exists(path):
            cl.load_settings(path)
            return True
    except Exception as e:
        print(f"[session load] {e}")
    return False


# ============================================================
# تسجيل الدخول
# ============================================================

def login_instagram(username, password):
    """
    يسجّل الدخول لإنستكرام.
    - جرّب الجلسة المحفوظة أول
    - إذا فشلت، سجّل من جديد
    - احفظ الجلسة للاستخدام التالي
    """
    cl = Client()

    # إعدادات إضافية لتقليل الحظر
    cl.set_device({
        "app_version": "269.0.0.18.75",
        "android_version": 26,
        "android_release": "8.0.0",
        "dpi": "480dpi",
        "resolution": "1080x1920",
        "manufacturer": "OnePlus",
        "device": "devitron",
        "model": "6T Dev",
        "cpu": "qcom",
        "version_code": "314665256",
    })

    # 1. جرّب الجلسة
    if load_session(cl, username):
        try:
            cl.login(username, password)
            cl.get_timeline_feed()
            return cl, None
        except LoginRequired:
            print("[instagram] الجلسة منتهية، تسجيل من جديد")
        except Exception as e:
            print(f"[instagram] فشل الجلسة: {e}")

    # 2. تسجيل من جديد
    try:
        cl.login(username, password)
        save_session(cl, username)
        return cl, None
    except ChallengeRequired:
        return None, "الحساب يحتاج تحقق (Challenge). افتح الحساب من التطبيق أولاً."
    except PleaseWaitFewMinutes:
        return None, "إنستكرام يطلب الانتظار قليلاً. جرّب بعد 15 دقيقة."
    except Exception as e:
        return None, f"فشل تسجيل الدخول: {str(e)}"


# ============================================================
# النشر
# ============================================================

def post_photo(username, password, image_path, caption):
    """ينشر صورة"""
    if not os.path.exists(image_path):
        return False, "الصورة مو موجودة"

    for attempt in range(MAX_RETRIES):
        try:
            cl, error = login_instagram(username, password)
            if error:
                return False, error

            media = cl.photo_upload(image_path, caption)
            return True, None

        except RateLimitError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            return False, "تم الوصول لحد النشر. جرّب بعد ساعة."
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(10)
                continue
            return False, f"فشل النشر: {str(e)}"

    return False, "فشل بعد عدة محاولات"


def post_carousel(username, password, image_paths, caption):
    """ينشر Carousel (عدة صور)"""
    if not image_paths or len(image_paths) < 2:
        return False, "تحتاج صورتين على الأقل"

    for path in image_paths:
        if not os.path.exists(path):
            return False, f"الصورة مو موجودة: {path}"

    try:
        cl, error = login_instagram(username, password)
        if error:
            return False, error

        media = cl.album_upload(image_paths, caption)
        return True, None
    except Exception as e:
        return False, f"فشل النشر: {str(e)}"


# ============================================================
# فحص الحساب
# ============================================================

def check_account(username, password):
    """يفحص إذا الحساب شغال"""
    cl, error = login_instagram(username, password)
    if error:
        return False, error
    try:
        info = cl.user_info(cl.user_id)
        return True, {
            "username": info.username,
            "full_name": info.full_name,
            "followers": info.follower_count,
            "following": info.following_count,
            "posts": info.media_count,
        }
    except Exception as e:
        return False, str(e)