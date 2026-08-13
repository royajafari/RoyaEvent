import { create } from "zustand";

import type { UserOut } from "@/lib/api-client";

type AuthState = {
  accessToken: string | null;
  user: UserOut | null;
  setAccessToken: (token: string | null) => void;
  setUser: (user: UserOut | null) => void;
  clear: () => void;
};

// توکن دسترسی فقط در حافظه نگه داشته می‌شود (نه localStorage) — بخش ۷ پلن
// معماری: محافظت در برابر XSS. Refresh token در کوکی httpOnly سمت سرور است.
// user برای نمایش‌های سبک (مثل آواتار کنار لینک پروفایل در هدر) نگه داشته
// می‌شود؛ منبع حقیقت واقعی همیشه GET /auth/me است.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAccessToken: (token) => set({ accessToken: token }),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, user: null }),
}));
