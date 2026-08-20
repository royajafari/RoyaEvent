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


def setup_json_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
