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
