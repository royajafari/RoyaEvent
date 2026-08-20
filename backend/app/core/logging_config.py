"""لاگ ساختاریافته JSON (فاز ۹) — بدون این، خروجی لاگ متن‌ساده‌ی قبلی
(`"%(asctime)s %(name)s %(message)s"`) برای Promtail/Loki قابل پارس‌کردن
فیلد به فیلد نیست (سطح لاگ/logger name فقط با regex شکننده قابل استخراجه).
یک stdlib `logging.Formatter` سفارشی، بدون وابستگی جدید (مثل python-json-logger)."""

from __future__ import annotations

import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_json_logging(level: int = logging.INFO, file_path: str | None = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if file_path:
        # فقط در production ست می‌شه (فاز ۱۱) — بک‌اند/worker اونجا هر دو تو
        # کانتینر جدا اجرا می‌شن، پس دایرکتوری infra/logs/ مشترک رو mount
        # می‌کنن تا Promtail (که docker socket نداره، طبق تصمیم امنیتی این
        # پروژه) بتونه فایل رو با static scrape بخونه — دقیقاً همون الگوی
        # dev (نگاه کن به infra/promtail/promtail-config.yml).
        handlers.append(logging.FileHandler(file_path, encoding="utf-8"))
    for handler in handlers:
        handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = handlers
    root.setLevel(level)
