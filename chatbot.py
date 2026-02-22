import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional
from urllib import error, request


DEFAULT_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class MatchResult:
    question: str
    answer: str
    score: float


class JsonKnowledgeBase:
    """Loads FAQ-like question/answer data from JSON and finds best match."""

    def __init__(self, file_path: str, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        self.file_path = file_path
        self.threshold = threshold
        self.items: List[Dict[str, str]] = self._load_items()

    def _load_items(self) -> List[Dict[str, str]]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON knowledge base باید یک لیست از آبجکت‌ها باشد.")

        cleaned = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict) or "question" not in item or "answer" not in item:
                raise ValueError(
                    f"آیتم شماره {idx} ساختار درست ندارد. هر آیتم باید question و answer داشته باشد."
                )
            cleaned.append({"question": str(item["question"]), "answer": str(item["answer"])})
        return cleaned

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def find_best_match(self, query: str) -> Optional[MatchResult]:
        normalized_query = self._normalize(query)
        best: Optional[MatchResult] = None

        for item in self.items:
            normalized_question = self._normalize(item["question"])
            score = SequenceMatcher(None, normalized_query, normalized_question).ratio()

            if best is None or score > best.score:
                best = MatchResult(question=item["question"], answer=item["answer"], score=score)

        if best and best.score >= self.threshold:
            return best
        return None


class PurchaseTrackingClient:
    """Simple API client for fetching purchase tracking status from backend."""

    def __init__(self, base_url: str, timeout: int = 10):
        if not base_url:
            raise ValueError("API base URL تنظیم نشده است.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_token = os.getenv("API_TOKEN", "")

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/orders/{order_id}/tracking"
        headers = {"Accept": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        req = request.Request(endpoint, headers=headers, method="GET")
        with request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)


class SmartChatBot:
    def __init__(self, kb: JsonKnowledgeBase, tracking_client: Optional[PurchaseTrackingClient] = None):
        self.kb = kb
        self.tracking_client = tracking_client

    def handle_message(self, message: str) -> str:
        message = message.strip()
        if not message:
            return "لطفا پیام خالی ارسال نکنید."

        if message.startswith("پیگیری"):
            parts = message.split(maxsplit=1)
            if len(parts) < 2:
                return "برای پیگیری خرید، از فرمت `پیگیری <شماره سفارش>` استفاده کنید."
            order_id = parts[1].strip()
            return self._track_order(order_id)

        match = self.kb.find_best_match(message)
        if match:
            return f"{match.answer}\n(درجه اطمینان: {match.score:.2f})"

        return "پاسخ دقیقی پیدا نکردم. لطفا سوال را واضح‌تر بپرسید یا به پشتیبانی وصل شوید."

    def _track_order(self, order_id: str) -> str:
        if not self.tracking_client:
            return "امکان پیگیری سفارش فعال نیست. لطفا API_BASE_URL را تنظیم کنید."

        try:
            payload = self.tracking_client.get_order_status(order_id)
        except error.HTTPError as exc:
            return f"خطا در دریافت وضعیت سفارش. کد خطا: {exc.code}"
        except (error.URLError, TimeoutError, json.JSONDecodeError):
            return "ارتباط با سرور پیگیری خرید برقرار نشد یا پاسخ معتبر نبود."

        status = payload.get("status", "نامشخص")
        last_update = payload.get("last_update", "نامشخص")
        carrier = payload.get("carrier", "نامشخص")
        tracking_code = payload.get("tracking_code", "نامشخص")

        return (
            "نتیجه پیگیری سفارش:\n"
            f"- وضعیت: {status}\n"
            f"- آخرین بروزرسانی: {last_update}\n"
            f"- شرکت حمل: {carrier}\n"
            f"- کد رهگیری: {tracking_code}"
        )


def main() -> None:
    kb_path = os.getenv("KB_FILE", "knowledge_base.json")
    api_base_url = os.getenv("API_BASE_URL", "")

    kb = JsonKnowledgeBase(kb_path)
    tracking_client = PurchaseTrackingClient(api_base_url) if api_base_url else None
    bot = SmartChatBot(kb, tracking_client)

    print("چت‌بات آماده است. برای خروج، `exit` یا `quit` را وارد کنید.")
    while True:
        user_input = input("شما: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("ربات: خداحافظ 👋")
            break

        reply = bot.handle_message(user_input)
        print(f"ربات: {reply}")


if __name__ == "__main__":
    main()
