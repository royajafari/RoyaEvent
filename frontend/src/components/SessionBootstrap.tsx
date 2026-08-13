"use client";

import { useEffect } from "react";

import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

// یک promise سطح‌ماژول (نه state داخل کامپوننت) که تضمین می‌کنه فراخوانی
// /auth/refresh حداکثر یک‌بار در طول عمر صفحه اتفاق بیفته. چون refresh token
// چرخشیه (هر فراخوانی، توکن قبلی رو باطل و یکی جدید صادر می‌کنه)، دو
// فراخوانی هم‌زمان با همون کوکی اولیه باعث می‌شه فراخوانی دوم به‌عنوان
// «استفاده‌ی مجدد از توکن باطل‌شده» تشخیص داده بشه و کل session باطل بشه.
// React StrictMode در dev دقیقاً همین سناریو رو با دوبار اجرای effect ایجاد
// می‌کنه — بدون این کش، هر بار در dev لاگین بعد از رفرش صفحه از بین می‌رفت.
let bootstrapPromise: Promise<string | null> | null = null;

function bootstrapSession(): Promise<string | null> {
  if (!bootstrapPromise) {
    bootstrapPromise = authApi
      .refresh()
      .then((res) => res.access_token)
      .catch(() => null);
  }
  return bootstrapPromise;
}

// access token فقط در حافظه است (auth-store.ts) و با هر رفرش صفحه پاک می‌شه؛
// این کامپوننت موقع لود اولیه‌ی سایت، با کوکی httpOnly رفرش‌توکن سعی می‌کنه
// یه access token جدید بگیره تا session کاربر لاگین‌شده بعد از رفرش صفحه از
// دست نره. اگه کوکی معتبری نباشه (بازدیدکننده‌ی لاگین‌نکرده)، بی‌صدا نادیده
// گرفته می‌شه — این حالت طبیعیه، نه خطا.
export function SessionBootstrap() {
  const setAccessToken = useAuthStore((s) => s.setAccessToken);

  useEffect(() => {
    bootstrapSession().then((token) => {
      if (token) setAccessToken(token);
    });
  }, [setAccessToken]);

  return null;
}

export default SessionBootstrap;
