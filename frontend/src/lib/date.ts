// نمایش تاریخ/ساعت شمسی (جلالی) با Intl بومی — بدون نیاز به کتابخانه‌ی
// جانبی؛ Node/مرورگرهای مدرن از calendar=persian با ICU کامل پشتیبانی
// می‌کنند. ذخیره‌سازی/انتقال همیشه UTC/میلادی می‌ماند (فقط نمایش شمسی است).

export function formatJalaliDateTime(iso: string): string {
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    dateStyle: "long",
    timeStyle: "short",
  }).format(new Date(iso));
}

export function formatJalaliDate(iso: string): string {
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    dateStyle: "long",
  }).format(new Date(iso));
}

export function formatJalaliShort(iso: string): string {
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}

// جلسه «در حال ارائه» است اگر الان بین شروع و پایان (شروع + مدت) باشیم —
// صرفاً برای نمایش برچسب استفاده می‌شه، تصمیم واقعی خرید/ثبت‌نام هیچ
// محدودیت زمانی نداره (سمت بک‌اند create_order فقط ظرفیت/وضعیت رویداد
// رو چک می‌کنه، نه زمان جلسه).
export function isSessionLive(startsAtIso: string, durationMinutes: number): boolean {
  const start = new Date(startsAtIso).getTime();
  const end = start + durationMinutes * 60 * 1000;
  const now = Date.now();
  return now >= start && now <= end;
}
