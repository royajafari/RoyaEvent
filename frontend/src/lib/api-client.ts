export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function request<T>(
  path: string,
  options: RequestInit & { accessToken?: string | null } = {},
): Promise<T> {
  const { accessToken, headers, ...rest } = options;
  const isFormData = typeof FormData !== "undefined" && rest.body instanceof FormData;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    credentials: "include", // برای ارسال/دریافت کوکی httpOnly رفرش‌توکن
    headers: {
      // برای FormData نباید Content-Type دستی ست بشه؛ خود مرورگر boundary لازم رو اضافه می‌کنه
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.message ?? body.detail ?? "خطای غیرمنتظره رخ داد");
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

// fetch امکان دنبال‌کردن پیشرفت آپلود رو نمی‌ده؛ برای فایل‌های حجیم (مثل کلیپ
// تبلیغاتی) از XMLHttpRequest استفاده می‌کنیم تا درصد آپلود رو نشون بدیم.
export function uploadFileWithProgress<T>(
  path: string,
  file: File,
  accessToken: string,
  onProgress?: (percent: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
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
