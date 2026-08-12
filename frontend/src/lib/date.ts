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
