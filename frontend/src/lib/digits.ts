// کیبورد فارسی ویندوز پیش‌فرض عدد رو با ارقام فارسی/عربی تایپ می‌کنه، نه
// ASCII — فیلدهای عددی حیاتی (کد تأیید OTP، شماره موبایل) باید قبل از
// ارسال به بک‌اند نرمال بشن، وگرنه مقایسه‌ی هش/رجکس بک‌اند (که ASCII
// فرض می‌کنه) بی‌صدا شکست می‌خوره — پیام خطا هم عمداً کلی‌ست (OTP)، پس
// این باگ راحت با «کد منقضی شده» اشتباه گرفته می‌شه.
const PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
const ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩";

export function toEnglishDigits(value: string): string {
  return value.replace(/[۰-۹٠-٩]/g, (char) => {
    const persianIndex = PERSIAN_DIGITS.indexOf(char);
    if (persianIndex !== -1) return String(persianIndex);
    const arabicIndex = ARABIC_INDIC_DIGITS.indexOf(char);
    return arabicIndex !== -1 ? String(arabicIndex) : char;
  });
}

// فقط برای *نمایش* به کاربر (نه ارسال به بک‌اند) — عکس toEnglishDigits،
// هیچ‌وقت روی مقداری که به سرور می‌ره صدا زده نشه.
export function toPersianDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (char) => PERSIAN_DIGITS[Number(char)]);
}
