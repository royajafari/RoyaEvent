"use client";

import { useEffect } from "react";

import { startOnboardingTourIfFirstVisit } from "@/lib/onboarding-tour";

// فقط منطق اجرای خودکار تور برای بازدید اول؛ چیزی رندر نمی‌کنه. دکمه‌ی
// تکرار دستی تور در SiteHeader است (startOnboardingTour مستقیم).
export function OnboardingTour() {
  useEffect(() => {
    const timer = setTimeout(startOnboardingTourIfFirstVisit, 600);
    return () => clearTimeout(timer);
  }, []);

  return null;
}

export default OnboardingTour;
