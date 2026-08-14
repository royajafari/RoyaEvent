"use client";

import DatePicker, { type DateObject } from "react-multi-date-picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import TimePicker from "react-multi-date-picker/plugins/time_picker";

// تقویم/ساعت شمسی برای فیلدهای زمان‌بندی جلسه — input نیتیو
// type="datetime-local" مرورگر همیشه میلادیه و راهی برای عوض‌کردنش نیست
// (محدودیت خود مرورگرهاست، نه چیزی که با CSS/locale صفحه حل بشه). مقدار
// ورودی/خروجی این کامپوننت همیشه یک رشته‌ی ISO میلادی است (سازگار با بقیه‌ی
// فرم و بک‌اند)؛ فقط نمایش با تقویم جلالی انجام می‌شه.
const INPUT_CLASS =
  "h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base text-right transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm dark:bg-input/30";

// لوکیل persian_fa برای هدر تقویم به‌صورت پیش‌فرض شکل خلاصه‌ی هر روز رو
// نشون می‌ده (["شنبه","شن"] → "شن")، نه اسم کامل؛ با override این prop
// اسم کامل اجباری می‌شه. ترتیب باید دقیقاً با شروع هفته از شنبه هماهنگ باشه.
const FULL_WEEK_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"];

export function JalaliDateTimePicker({
  id,
  value,
  onChange,
  required,
}: {
  id?: string;
  value: string;
  onChange: (isoString: string) => void;
  required?: boolean;
}) {
  return (
    <span className="relative block w-full">
      <DatePicker
        id={id}
        value={value ? new Date(value) : null}
        onChange={(date: DateObject | null) => onChange(date ? date.toDate().toISOString() : "")}
        calendar={persian}
        locale={persian_fa}
        weekDays={FULL_WEEK_DAYS}
        format="YYYY/MM/DD HH:mm"
        plugins={[<TimePicker key="time-picker" hideSeconds position="bottom" />]}
        inputClass={INPUT_CLASS}
        containerClassName="w-full"
        calendarPosition="bottom-right"
        required={required}
      />
      {required && (
        <span
          aria-hidden="true"
          title="اجباری"
          className="pointer-events-none absolute top-0 right-0 z-10 h-2.5 w-2.5 bg-destructive"
          style={{ clipPath: "polygon(100% 0, 0 0, 100% 100%)" }}
        />
      )}
    </span>
  );
}

export default JalaliDateTimePicker;
