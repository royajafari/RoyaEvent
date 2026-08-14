# فاز ۴ — جستجوی محتوایی (ChromaDB) + صفحه‌ی اصلی

وضعیت: ✅ کامل (بک‌اند + فرانت‌اند)، تست‌شده (لاگ کامل مصنوعی/مقلد برای embedding — بدون نیاز به مدل واقعی در CI)، لینت/build تمیز.

## نتیجه‌ی فازهای قبل (خلاصه)

فاز ۰: اسکلت پروژه. فاز ۱: احراز هویت OTP-only + JWT چرخشی. فاز ۲: CRUD رویداد کامل. فاز ۳: بلیط/سفارش/تخفیف/علاقه‌مندی/دنبال‌کردن + یک سری addendum بزرگ بعد از فاز (کلیپ تبلیغاتی، تور آموزشی، TLS/Docker، تکمیل پروفایل اجباری، سیستم مدرس، دنبال‌کردن enrich‌شده، آواتار کاربر). جمعاً ۱۹۸ تست پاس تا قبل از این فاز. جزئیات: [`spec0.md`](spec0.md)…[`spec3.md`](spec3.md).

## هدف

جستجوی معنایی/چندزبانه روی عنوان+توضیحات رویداد (نه فقط تطبیق دقیق کلمه)، همراه با تشخیص جستجوی نام برگزارکننده/مدرس («بخش افراد»)، و یک endpoint واحد و Redis-cached برای بخش‌های الگوریتمی صفحه‌ی اصلی.

## چیزی که ساخته شد

### بک‌اند

- **نصب وابستگی‌های سنگین:** `chromadb==0.5.23` و `sentence-transformers==3.3.1` در `requirements.txt` uncomment شدن (از فاز ۰ عمداً کامنت بودن). **torch نسخه‌ی CPU-only جدا و اول نصب شد** (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) تا موقع نصب `sentence-transformers`، pip سراغ wheel غول‌پیکر CUDA نره — روی شبکه‌ی ناپایدار این محیط تفاوت بزرگی داشت.
- **`app/search/`** (ماژول جدید):
  - `chroma_client.py` — کلاینت embedded ChromaDB (`PersistentClient`, مسیر از `settings.chroma_persist_dir`، از فاز ۰ در config.py آماده بود)، `@lru_cache` روی خود کلاینت.
  - `embeddings.py` — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (چندزبانه، فارسی رو پشتیبانی می‌کنه)، لود مدل تنبل (فقط موقع اولین `embed_text()` واقعی، نه موقع import ماژول) تا import ساده این فایل هزینه‌ی دانلود/لود نداشته باشه.
  - `indexer.py` — `sync_event_index(event)`: تصمیم می‌گیره upsert کنه یا از ایندکس حذف کنه، **فقط بر اساس `status==PUBLISHED and visibility==PUBLIC`** (طبق قاعده‌ی دائمی امنیتی فاز ۲: DRAFT/CANCELLED/PRIVATE هرگز نباید از هیچ مسیر عمومی — از جمله جستجو — قابل دیدن باشن).
  - `reindex.py` — اسکریپت idempotent برای بازسازی کامل ایندکس از روی رویدادهای PUBLISHED+PUBLIC موجود در SQLite (`python -m app.search.reindex`) — لازم چون `sync_event_index` فقط از این به بعد موقع publish/update/cancel صدا زده می‌شه، رویدادهای منتشرشده‌ی قبل از این فاز باید یک‌بار دستی reindex بشن.
- **قلاب ایندکس:** `event_service.py` — `publish_event`/`cancel_event` همیشه `sync_event_index` رو صدا می‌زنن؛ `update_event` فقط اگه رویداد از قبل PUBLISHED باشه (چون تغییر عنوان/توضیحات باید embedding رو تازه کنه).
- **`GET /search?q=&category_id=&format=`** (`search_service.py`): دو بخش مستقل، هردو همیشه اجرا می‌شن (نه either/or):
  - `search_people`: تطبیق prefix (`ILIKE 'query%'`) روی نام مدرس‌ها + برگزارکننده‌هایی که حداقل یک رویداد PUBLISHED+PUBLIC دارن.
  - `search_events`: `embed_text(query)` → `collection.query()` در Chroma → گرفتن idهای برگشتی → فیلتر زنده روی SQLite (status/visibility/category/format) → مرتب‌سازی نهایی طبق همون ترتیب شباهت Chroma (نه ترتیب پیش‌فرض SQL). **SQLite همیشه منبع حقیقت نهایی برای فیلدهای قابل فیلتر می‌مونه**، Chroma فقط شباهت/ترتیب می‌ده.
  - `GET /search/suggestions?q=` — autocomplete سبک (`ILIKE` ساده روی عنوان، بدون embedding) برای پیشنهاد حین تایپ.
  - Rate limit: `30/دقیقه` روی `/search` طبق بخش ۶ architecture.md.
- **`GET /home/sections`** (`home_service.py`) — یک endpoint، Redis-cached (TTL ۵ دقیقه، کلید `home:sections`)، ۵ بخش با داده‌ی **واقعی** (نه فیک):
  - `popular_events` (view_count DESC), `latest_events` (published_at DESC), `featured_events` (is_featured=true، با fallback به تازه‌ترین‌ها اگه کمتر از ۶ تا ویژه باشه — طبق بخش ۱۰ architecture.md), `popular_instructors` (follower_count DESC، از قبل در فاز ۳/addendum ساخته شده بود), `popular_organizers` (follower_count DESC، جدید).
  - **عمداً دو بخش از پلن اصلی ساخته نشدن:** «برترین وبینارها بر اساس امتیاز» (سیستم امتیازدهی فاز ۷ هنوز نیست، `rating_avg` همه صفره) و «محبوب‌ترین ویدیوهای ضبط‌شده» (مفهوم «ضبط رویداد گذشته» اصلاً در مدل داده نیست — `promo_video_url` چیز دیگه‌ایه). ساختن این دو با داده‌ی خالی/فیک بدتر از نبودشونه.
- **`GET /events`** یک پارامتر جدید گرفت: `featured: bool | None` — برای صفحه‌ی «مشاهده همه»ی بخش ویژه (بدون fallback؛ فقط رویدادهای واقعاً is_featured).
- **کاهش `refresh_token_expire_days` از ۳۰ به ۱** (تصمیم کاربر، بعد از بحث درباره‌ی مدت‌زمان معقول نشست) — در `config.py` و `.env.example`.
- **تست‌ها (۱۴ تست جدید، ۲۱۲ در مجموع):** `test_search_api.py` (۸ تست) و `test_home_api.py` (۵ تست، شامل یک تست که صریحاً رفتار کش رو تأیید می‌کنه: بعد از publish یه رویداد جدید، تا وقتی TTL کش نگذشته نتیجه باید عوض نشه) و یک تست برای فیلتر `featured` در `test_events_api.py`.
  - **نکته‌ی کلیدی تست:** `conftest.py` یک fixture خودکار (`_mock_search_indexing`) اضافه شد که `sync_event_index` رو برای **کل تست‌سوییت** no-op می‌کنه — بدون این، هر تستی که رویدادی publish/cancel می‌کرد (یعنی اکثر تست‌های events/orders/social/instructors) سعی می‌کرد مدل embedding واقعی رو لود کنه (کند/شکننده/نیازمند شبکه). تست‌های اختصاصی جستجو (`test_search_api.py`) خودشون این mock رو override می‌کنن و به‌جاش از `chromadb.EphemeralClient()` (in-memory) + یک تابع embedding قلابی و سریع (bag-of-words هش‌شده، بدون دانلود مدل) استفاده می‌کنن — نتیجه: کل تست‌سوییت هنوز چند ثانیه طول می‌کشه، نه چند دقیقه.

### فرانت‌اند

- `lib/search-api.ts` (کلاینت) + `lib/search-server.ts` (SSR) + `lib/home-server.ts` (SSR برای `/home/sections`).
- `app/search/page.tsx` — SSR، بخش «افراد» (مدرس‌ها لینک‌دار به پروفایلشون، برگزارکننده‌ها فقط badge چون صفحه‌ی عمومی برگزارکننده هنوز نیست) بالای نتایج رویداد.
- نوار جستجو در `SiteHeader.tsx` — فرم ساده، submit → `router.push('/search?q=...')`.
- **`components/EventCarousel.tsx`** — کاروسل با دو دکمه‌ی فلش (چپ/راست) + لینک «مشاهده همه»، طبق طرح اسکرین‌شاتی که کاربر از یک سایت رقیب فرستاد. صفحه‌ی اصلی (`app/page.tsx`) حالا فقط یک فراخوانی (`homeServer.getSections()`) داره و سه بخش رویداد (محبوب/آخرین/ویژه) رو با این کاروسل نشون می‌ده؛ مدرس‌های محبوب/برگزارکننده‌های محبوب هنوز گرید ساده‌ن (کاروسل فقط برای بخش‌های رویداد درخواست شده بود).
- **`components/BackToTopButton.tsx`** — دکمه‌ی شناور «برو بالا»، بعد از عبور از ۴۰۰px اسکرول ظاهر می‌شه، در layout ریشه.
- `app/events/page.tsx` حالا `sort`/`featured` رو هم از URL می‌خونه (برای لینک‌های «مشاهده همه» از کاروسل).

## نکات/دام‌های این فاز

- **`collection.query()` در ChromaDB وقتی collection خالیه (هیچ سندی upsert نشده) خطا می‌ده، نه لیست خالی برمی‌گردونه** — `search_events` قبل از query چک می‌کنه `collection.count() == 0` و زودتر لیست خالی برمی‌گردونه.
- **مرتب‌سازی بعد از `filter(Event.id.in_(ids))` در SQLAlchemy ترتیب `ids` رو حفظ نمی‌کنه** — باید صریح با یه dict رتبه (`{event_id: index}`) دوباره `sort()` بشه، وگرنه ترتیب شباهت Chroma گم می‌شه و نتایج به ترتیب دلخواه SQLite برمی‌گردن.
- **مدل embedding واقعی (~۴۷۰ مگابایت از HuggingFace Hub) روی شبکه‌ی این محیط چند بار وسط دانلود قطع شد** (`ChunkedEncodingError`) — دقیقاً همون الگوی دام #۱۶ در CLAUDE.md (شبکه‌ی ناپایدار). چون `huggingface_hub` دانلود ناقص رو کش و resume می‌کنه، فقط دوباره اجرای همون دستور (`python -m app.search.reindex`) کافی بود، نیازی به پاک‌کردن کش نبود.
- **بک‌فیل رویدادهای منتشرشده‌ی قبل از این فاز اتوماتیک نیست** — `sync_event_index` فقط از لحظه‌ی نصب این فاز به بعد، موقع publish/update/cancel صدا زده می‌شه. برای این‌که رویدادهای قبلاً منتشرشده هم قابل جستجو باشن، یک‌بار `python -m app.search.reindex` باید دستی اجرا بشه (اجرا شد، جزئیات کامل دانلود مدل تو راستی‌آزمایی).
- **کاروسل RTL:** جهت مثبت/منفی `scrollBy({left})` همیشه فیزیکیه (مثبت=راست، منفی=چپ)، مستقل از `dir="rtl"`/`dir="ltr"` — فقط مقدار *شروع* `scrollLeft` و بازه‌ش در RTL فرق می‌کنه (می‌تونه منفی باشه)، نه علامت delta که به `scrollBy` می‌دی. این قرارداد در Chrome/Firefox/Edge مدرن صادقه؛ Safari تاریخاً یه رفتار متفاوت داره (محدودیت شناخته‌شده‌ی مرورگر، نه باگ کامپوننت — قابل تست بصری واقعی در این sandbox نیست چون Playwright/Chromium در دسترس نیست، دام #۸ قدیمی).

## راستی‌آزمایی

بک‌اند و فرانت هر دو real dev server، `212 passed` (`pytest`)، `ruff check .` و `npx eslint src --max-warnings=0` هر دو تمیز، `npm run build` موفق (بعدش dev server با `.next` تازه ری‌استارت شد طبق دام #۱۷ CLAUDE.md). `curl` مستقیم روی `/api/v1/home/sections` نتایج واقعی از DB دورن (نه mock)، `/api/v1/search` و `/api/v1/search/suggestions` هم مسیرهاشون تأیید شد. بک‌فیل رویدادهای قدیمی (`python -m app.search.reindex`) به‌خاطر کندی دانلود مدل embedding روی شبکه‌ی این محیط، هنوز کامل تأیید نشده بود — منطق ایندکس/جستجو خودش با تست‌های mock‌شده (embedding قلابی + Chroma in-memory) کامل پوشش داده شده، بدون وابستگی به این دانلود.

### بعد از فاز — باگ کشف‌شده حین تست بصری زنده‌ی کاربر

**پاک‌کردن نوار جستجو از خود صفحه‌ی نتایج هیچ اتفاقی نمی‌افتاد** — کاربر متن جستجو رو با بک‌اسپیس/دکمه‌ی X پاک می‌کرد ولی رو همون صفحه‌ی نتیجه‌ی خالی می‌موند (فرم فقط روی submit صریح navigate می‌کرد، نه روی خالی‌شدن مقدار). فیکس: `SiteHeader.tsx` با `usePathname()` چک می‌کنه اگه کاربر همین الان تو `/search`ه و مقدار input خالی شد، خودکار به `/events` (لیست کامل) redirect می‌کنه.

## Commitهای مرتبط

`7d9bf39` (شروع فاز ۴: زیرساخت جستجو + چند فیکس UX)، `a1e2fb4` (تکمیل بک‌اند: endpoint جستجو + home/sections)، `7b7ae81` (تکمیل فرانت: نوار جستجو + کاروسل)، `5575453` (مستندسازی)، `99ab987` (فیکس پاک‌کردن نوار جستجو)
