"""اتصال Mongo برای آنالیتیکس رفتاری (فاز ۸) — MongoDB منبع رکورد اصلی
نیست، فقط لاگ خام رفتار کاربر (بخش ۳ پلن معماری). serverSelectionTimeoutMS
کوتاه عمداً تنظیم شده تا اگر Mongo پایین بود، درخواست اصلی کاربر (که هرگز
نباید به یک beacon تحلیلی وابسته بمونه) طولانی معطل نمونه."""

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings


@lru_cache
def get_mongo_db() -> Database:
    settings = get_settings()
    client: MongoClient = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
    return client[settings.mongo_db_name]
