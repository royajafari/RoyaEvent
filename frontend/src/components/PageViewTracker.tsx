"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { track } from "@/lib/track";

// بدون UI — فقط هر تغییر مسیر رو به‌عنوان page_view ثبت می‌کنه. مثل
// SessionBootstrap، track() از یک ماژول *دیگه* import شده (نه تابع محلی
// این کامپوننت)، پس صدا زدنش از دل effect با react-hooks/set-state-in-effect
// تداخل نداره.
export function PageViewTracker() {
  const pathname = usePathname();

  useEffect(() => {
    track("page_view", { path: pathname });
  }, [pathname]);

  return null;
}

export default PageViewTracker;
