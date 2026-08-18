// معادل فرانتی app/core/calendar.py — تابع محض بدون OAuth/API call، پس نیازی
// به لاگین یا ثبت‌نام برای «افزودن به تقویم» روی صفحه‌ی عمومی رویداد نیست
// (برخلاف افزودن به تقویم بعد از خرید بلیط که چون به یک registration خاص
// وصله، نیاز به لاگین داره — این همون منطق رو برای بازدیدکننده‌ی مهمان تکرار می‌کنه).
function toGoogleDate(iso: string): string {
  return new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

export function buildGoogleCalendarLink({
  title,
  description,
  location,
  startsAtIso,
  durationMinutes,
}: {
  title: string;
  description: string;
  location: string;
  startsAtIso: string;
  durationMinutes: number;
}): string {
  const start = new Date(startsAtIso);
  const end = new Date(start.getTime() + durationMinutes * 60 * 1000);
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: title,
    dates: `${toGoogleDate(start.toISOString())}/${toGoogleDate(end.toISOString())}`,
    details: description,
    location,
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}
