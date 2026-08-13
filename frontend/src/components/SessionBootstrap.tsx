"use client";

import { useEffect } from "react";

import { refreshAccessToken } from "@/lib/api-client";

// access token فقط در حافظه است (auth-store.ts) و با هر رفرش صفحه پاک می‌شه؛
// این کامپوننت موقع لود اولیه‌ی سایت، با کوکی httpOnly رفرش‌توکن سعی می‌کنه
// یه access token جدید بگیره تا session کاربر لاگین‌شده بعد از رفرش صفحه از
// دست نره. اگه کوکی معتبری نباشه (بازدیدکننده‌ی لاگین‌نکرده)، بی‌صدا نادیده
// گرفته می‌شه — این حالت طبیعیه، نه خطا.
//
// refreshAccessToken از lib/api-client.ts استفاده می‌شه (نه یه promise
// جدا این‌جا) چون همون guard تک‌پرواز رو با منطق retry-روی-۴۰۱ در
// request()/uploadFileWithProgress به اشتراک می‌ذاره — دو تا promise
// سطح‌ماژول جدا از هم اصلاً محافظت لازم در برابر رفرش هم‌زمان رو نمی‌دن.
export function SessionBootstrap() {
  useEffect(() => {
    refreshAccessToken();
  }, []);

  return null;
}

export default SessionBootstrap;
