# Smart JSON Chatbot (Python)

یک چت‌بات ساده و هوشمند که:

1. پاسخ سوالات متداول را از فایل `JSON` پیدا می‌کند.
2. پیگیری خرید مشتری را از طریق API بک‌اند دریافت می‌کند.

## اجرا

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python chatbot.py
```

## تنظیمات

- `KB_FILE`: مسیر فایل دانش JSON (پیش‌فرض: `knowledge_base.json`)
- `API_BASE_URL`: آدرس پایه API بک‌اند (مثال: `https://api.example.com`)
- `API_TOKEN`: (اختیاری) توکن Bearer برای احراز هویت API

## فرمت فایل دانش

```json
[
  {"question": "سوال اول", "answer": "پاسخ اول"},
  {"question": "سوال دوم", "answer": "پاسخ دوم"}
]
```

## نمونه استفاده

- سوال معمولی:
  - `ساعت کاری فروشگاه چیست؟`
- پیگیری سفارش:
  - `پیگیری 12345`

در حالت پیگیری، ربات API زیر را صدا می‌زند:

- `GET {API_BASE_URL}/orders/<order_id>/tracking`

و انتظار دارد JSON مشابه زیر دریافت کند:

```json
{
  "status": "در حال ارسال",
  "last_update": "2026-02-20T14:22:00Z",
  "carrier": "پست پیشتاز",
  "tracking_code": "IR-POST-998877"
}
```
