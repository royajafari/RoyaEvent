import { create } from "zustand";

type AuthState = {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
  clear: () => void;
};

// توکن دسترسی فقط در حافظه نگه داشته می‌شود (نه localStorage) — بخش ۷ پلن
// معماری: محافظت در برابر XSS. Refresh token در کوکی httpOnly سمت سرور است.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  setAccessToken: (token) => set({ accessToken: token }),
  clear: () => set({ accessToken: null }),
}));
