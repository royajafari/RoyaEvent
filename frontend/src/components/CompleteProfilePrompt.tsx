"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

// وقتی بک‌اند بگه «برای این کار باید ابتدا نام و نام خانوادگی خود را تکمیل
// کنید» (core/permissions.py: require_complete_profile — قبل از ایجاد
// رویداد یا خرید بلیط اجباریه)، به‌جای فقط نشون‌دادن پیام خطا، همین‌جا
// فرم نام رو نشون می‌دیم تا کاربر بدون رفتن به صفحه‌ی دیگه تکمیلش کنه.
export function CompleteProfilePrompt({ onCompleted }: { onCompleted: () => void }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !fullName.trim()) return;
    setError(null);
    setSubmitting(true);
    try {
      await authApi.updateProfile(fullName.trim(), accessToken);
      onCompleted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ذخیره‌ی نام");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="flex flex-col gap-3 rounded-md border border-dashed p-3"
    >
      <p className="text-sm">
        قبل از ادامه، لطفاً نام و نام خانوادگی خود را وارد کنید — این اطلاعات روی بلیط/فاکتور و به
        شرکت‌کننده‌ها نشون داده می‌شه.
      </p>
      <div className="flex flex-col gap-2">
        <Label htmlFor="complete-profile-name">نام و نام خانوادگی</Label>
        <Input
          id="complete-profile-name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
      </div>
      {error && <p className="text-destructive text-sm">{error}</p>}
      <Button type="submit" disabled={submitting || !fullName.trim()} className="w-fit">
        {submitting ? "در حال ذخیره..." : "ذخیره و ادامه"}
      </Button>
    </form>
  );
}

export default CompleteProfilePrompt;
