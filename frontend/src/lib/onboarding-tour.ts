import { driver } from "driver.js";
import "driver.js/dist/driver.css";

// تور آموزشی سایت — کارهای درخواستی در صف (CLAUDE.md). فقط برای بازدید اول
// خودکار اجرا می‌شه (چک با localStorage)؛ از هدر هم قابل تکرار دستیه.
const STORAGE_KEY = "royaevent_tour_completed";

function hasTourBeenSeen(): boolean {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(STORAGE_KEY) === "1";
}

function markTourSeen(): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, "1");
}

export function startOnboardingTour(): void {
  const tour = driver({
    showProgress: true,
    popoverClass: "roya-tour-popover",
    nextBtnText: "بعدی",
    prevBtnText: "قبلی",
    doneBtnText: "پایان",
    progressText: "{{current}} از {{total}}",
    onDestroyed: () => markTourSeen(),
    steps: [
      {
        element: "#tour-logo",
        popover: {
          title: "به رویا ایونت خوش آمدید 👋",
          description:
            "پلتفرم مدیریت و کشف رویداد/وبینار. این تور کوتاه امکانات اصلی سایت رو نشونتون می‌ده.",
        },
      },
      {
        element: "#tour-events",
        popover: {
          title: "رویدادها",
          description:
            "لیست همه‌ی وبینارها و رویدادهای منتشرشده — می‌تونید ببینید و ثبت‌نام کنید.",
        },
      },
      {
        element: "#tour-create",
        popover: {
          title: "ایجاد رویداد",
          description:
            "برگزارکننده‌اید؟ از این‌جا رویداد چندجلسه‌ای خودتون رو با بنر و کلیپ تبلیغاتی بسازید.",
        },
      },
      {
        element: "#tour-mine",
        popover: {
          title: "رویدادهای من",
          description: "رویدادهایی که ساختید رو این‌جا مدیریت، منتشر و شرکت‌کنندگانشون رو ببینید.",
        },
      },
      {
        element: "#tour-tickets",
        popover: {
          title: "بلیط‌های من",
          description: "بلیط‌هایی که خریدید، لغو ثبت‌نام و افزودن به تقویم گوگل از همین‌جا.",
        },
      },
      {
        element: "#tour-login",
        popover: {
          title: "ورود",
          description: "ورود فقط با کد یک‌بارمصرف پیامکی یا ایمیلی — بدون نیاز به پسورد.",
        },
      },
    ],
  });

  tour.drive();
}

export function startOnboardingTourIfFirstVisit(): void {
  if (hasTourBeenSeen()) return;
  startOnboardingTour();
}
