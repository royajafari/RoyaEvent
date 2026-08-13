import { useAuthStore } from "@/store/auth-store";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// access token فقط ۱۵ دقیقه اعتبار داره (بخش ۷ پلن)؛ اگه کاربر بیشتر از این
// روی یه صفحه بمونه بدون رفرش کامل، هر درخواستی ۴۰۱ می‌گیره. این guard
// «تک‌پرواز» (single-flight) دقیقاً همون promise سطح‌ماژول SessionBootstrap
// رو به اشتراک می‌ذاره — چون refresh token چرخشیه، دو تا فراخوانی هم‌زمان
// (مثلاً از دو درخواست موازی که هم‌زمان ۴۰۱ گرفتن) نباید هرکدوم جدا
// /auth/refresh رو صدا بزنن، وگرنه دومی reuse توکن باطل‌شده تشخیص داده
// می‌شه و کل session باطل می‌شه.
let refreshPromise: Promise<string | null> | null = null;

export function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((body: { access_token?: string } | null) => {
        const token = body?.access_token ?? null;
        if (token) {
          useAuthStore.getState().setAccessToken(token);
        } else {
          useAuthStore.getState().clear();
        }
        return token;
      })
      .catch(() => {
        useAuthStore.getState().clear();
        return null;
      })
      .finally(() => {
        // آزاد کردن promise بعد از قطعی‌شدن نتیجه (نه بلافاصله) تا دفعه‌ی
        // بعد که access token دوباره منقضی شد، واقعاً یه تلاش تازه انجام بشه.
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export async function request<T>(
  path: string,
  options: RequestInit & { accessToken?: string | null } = {},
): Promise<T> {
  const { accessToken, headers, ...rest } = options;
  const isFormData = typeof FormData !== "undefined" && rest.body instanceof FormData;

  const buildHeaders = (token?: string | null) => ({
    // برای FormData نباید Content-Type دستی ست بشه؛ خود مرورگر boundary لازم رو اضافه می‌کنه
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers,
  });

  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    credentials: "include", // برای ارسال/دریافت کوکی httpOnly رفرش‌توکن
    headers: buildHeaders(accessToken),
  });

  // فقط وقتی که اصلاً accessToken فرستاده بودیم (یعنی endpoint نیاز به auth
  // داشت) تلاش برای تازه‌کردن توکن و تکرار یک‌باره‌ی درخواست منطقی‌ئه — ۴۰۱
  // روی endpoint عمومی معنی دیگه‌ای داره (اصلاً auth نمی‌خواد).
  if (response.status === 401 && accessToken) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...rest,
        credentials: "include",
        headers: buildHeaders(newToken),
      });
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.message ?? body.detail ?? "خطای غیرمنتظره رخ داد");
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

function uploadFileOnce<T>(path: string, file: File, accessToken: string, onProgress?: (percent: number) => void) {
  return new Promise<T>((resolve, reject) => {
    const form = new FormData();
    form.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}${path}`);
    xhr.withCredentials = true;
    xhr.setRequestHeader("Authorization", `Bearer ${accessToken}`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve((xhr.responseText ? JSON.parse(xhr.responseText) : undefined) as T);
        return;
      }
      let message = "خطای غیرمنتظره رخ داد";
      try {
        const body = JSON.parse(xhr.responseText);
        message = body.message ?? body.detail ?? message;
      } catch {
        // پاسخ JSON نبود؛ پیام پیش‌فرض استفاده می‌شه
      }
      reject(new ApiError(xhr.status, message));
    };

    xhr.onerror = () => reject(new ApiError(0, "خطا در ارتباط با سرور"));
    xhr.send(form);
  });
}

// fetch امکان دنبال‌کردن پیشرفت آپلود رو نمی‌ده؛ برای فایل‌های حجیم (مثل کلیپ
// تبلیغاتی) از XMLHttpRequest استفاده می‌کنیم تا درصد آپلود رو نشون بدیم.
// همون منطق تازه‌کردن خودکار توکن منقضی‌شده‌ی request() این‌جا هم پیاده شده.
export async function uploadFileWithProgress<T>(
  path: string,
  file: File,
  accessToken: string,
  onProgress?: (percent: number) => void,
): Promise<T> {
  try {
    return await uploadFileOnce<T>(path, file, accessToken, onProgress);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        return uploadFileOnce<T>(path, file, newToken, onProgress);
      }
    }
    throw err;
  }
}

export type OTPRequestOut = {
  success: boolean;
  challenge_id: number;
  expires_in: number;
  retry_after: number;
};

export type OTPVerifyOut = {
  success: boolean;
  verified: boolean;
  access_token?: string | null;
  token_type?: string | null;
  message?: string | null;
};

export const authApi = {
  requestOtp: (destination: string, channel: "sms" | "email") =>
    request<OTPRequestOut>("/auth/otp/request", {
      method: "POST",
      body: JSON.stringify({ destination, channel, purpose: "login" }),
    }),

  resendOtp: (challengeId: number) =>
    request<OTPRequestOut>("/auth/otp/resend", {
      method: "POST",
      body: JSON.stringify({ challenge_id: challengeId }),
    }),

  verifyOtp: (challengeId: number, otp: string) =>
    request<OTPVerifyOut>("/auth/otp/verify", {
      method: "POST",
      body: JSON.stringify({ challenge_id: challengeId, otp }),
    }),

  refresh: () => request<{ access_token: string }>("/auth/refresh", { method: "POST" }),

  logout: () => request<{ success: boolean }>("/auth/logout", { method: "POST" }),

  me: (accessToken: string) => request("/auth/me", { accessToken }),
};
